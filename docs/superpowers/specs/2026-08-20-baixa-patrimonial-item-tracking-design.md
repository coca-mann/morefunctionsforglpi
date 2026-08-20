# Fluxo de Baixa Patrimonial — rastreio por item, confirmação e reprocessamento seletivo

Status: Aprovado para implementação
Data: 2026-08-20
App: `apps/reports` (com um novo campo em `apps/dbcom.GLPIConfig`, já existente)

## Contexto

O app `reports` gerencia `LaudoBaixa` (laudo de baixa patrimonial) e seus
`ItemLaudo` (equipamentos importados do GLPI para constar no laudo). Existe
hoje uma ação de admin, `atualizar_status_itens_no_glpi`
(`apps/reports/admin.py`), que aplica um `states_id` (configurado em
`GLPIConfig.glpi_status_baixa_id`) em todos os itens do laudo via API legada
v1 do GLPI.

A primeira versão dessa ação (implementada nesta mesma sessão) já resolveu:
validação de pré-condições (destinação preenchida, todos os itens com
`motivo_baixa`), um status agregado `LaudoBaixa.status`
(`RASCUNHO`/`PROCESSADO`) e trava de edição/exclusão quando o laudo está
`PROCESSADO`.

O que ficou capenga, e é o que este documento resolve:

1. **Rastreio só no nível do laudo** — não fica salvo qual item específico
   falhou nem por quê; só dá pra descobrir lendo o console do servidor.
2. **Sem confirmação antes de escrever no GLPI** — a ação dispara no
   primeiro clique, sem tela de revisão, para uma escrita irreversível num
   sistema externo.
3. **Sem auditoria de quem/quando processou** — não há registro de qual
   usuário disparou a baixa.
4. **Falha parcial reprocessa tudo de novo** — se 1 de 20 itens falha, a
   próxima tentativa reenvia os 20, incluindo os 19 que já tinham dado
   certo.

## Decisões (confirmadas com o usuário)

- Auditoria fica no **estado atual por item** (quem/quando/erro), não um
  histórico completo de tentativas anteriores.
- A tela de confirmação é uma **lista simples + status alvo** (padrão
  Django de página intermediária, sem pré-checagem ao vivo no GLPI).
- A trava de edição/exclusão passa a ser **por item** (`ItemLaudo.status`),
  não mais pelo agregado do laudo inteiro — permite reprocessar só os itens
  que falharam sem re-travar o laudo todo.

## Modelo de dados

### `ItemLaudo` (novos campos)

```python
STATUS_CHOICES = [
    ('PENDENTE', 'Pendente'),
    ('PROCESSADO', 'Processado no GLPI'),
    ('FALHA', 'Falha ao processar no GLPI'),
]

status = models.CharField(
    "Status no GLPI", max_length=15, choices=STATUS_CHOICES,
    default='PENDENTE', editable=False,
)
glpi_erro = models.TextField(
    "Último Erro (GLPI)", blank=True, editable=False,
    help_text="Mensagem de erro da última tentativa. Limpa quando o item é processado com sucesso.",
)
processado_em = models.DateTimeField(
    "Processado em", null=True, blank=True, editable=False,
)
processado_por = models.ForeignKey(
    User, verbose_name="Processado por", null=True, blank=True,
    editable=False, on_delete=models.SET_NULL, related_name='+',
)
```

Itens já existentes no banco ficam `PENDENTE` (default) — está correto
semanticamente, pois nenhum item foi processado de forma rastreável pelo
fluxo antigo.

### `LaudoBaixa.status` (redefinição de semântica, sem mudança de schema)

Continua `RASCUNHO`/`PROCESSADO`, mas passa a ser um **agregado
recomputado ao final de cada execução da ação**, não mais setado
manualmente dentro do `try/except`:

```python
todos_processados = not laudo.itens.exclude(status='PROCESSADO').exists()
if todos_processados:
    if laudo.status != 'PROCESSADO':
        laudo.status = 'PROCESSADO'
        laudo.data_baixa_glpi = timezone.now()
        laudo.save(update_fields=['status', 'data_baixa_glpi'])
elif laudo.status == 'PROCESSADO':
    # não deveria acontecer (itens PROCESSADO não podem ser apagados),
    # mas se acontecer, o agregado corrige sozinho na próxima execução
    laudo.status = 'RASCUNHO'
    laudo.save(update_fields=['status'])
```

`data_baixa_glpi` marca a primeira vez que o laudo bateu 100%; não é
re-setada em execuções subsequentes que não mudam esse estado.

### Migration

Uma migration nova em `reports` (`0008_...`) adicionando os 4 campos em
`ItemLaudo`. Sem necessidade de `RunPython` — os defaults cobrem o dado
existente.

## Enforcement da trava (camada de model, não de UI)

`ItemLaudo.save()`/`delete()` (já existem, ver `apps/reports/models.py`)
trocam a condição de `self.laudo.status == 'PROCESSADO'` para
`self.status == 'PROCESSADO'`. Essa é a fonte da verdade — vale para o
admin, para `manage.py shell`, para qualquer código futuro que toque no
model diretamente.

**Limitação técnica aceita conscientemente**: `TabularInline` do Django
não expõe permissão de exclusão por linha — `has_delete_permission` do
inline recebe o objeto **pai** (`LaudoBaixa`), não a linha (`ItemLaudo`),
então o checkbox "excluir" do formset é tudo-ou-nada por inline, não por
linha. Não vamos construir um formset customizado com JS para
esconder/desabilitar o checkbox linha a linha agora — a trava do model já
impede a exclusão de fato (o usuário vê um erro de validação ao tentar
salvar/apagar uma linha travada). Ganho de UX (esconder o checkbox antes
do clique) fica de fora deste escopo; revisitar se o uso real mostrar que
isso confunde os usuários.

`ItemLaudoInline.get_readonly_fields`/`has_delete_permission` (que hoje
checam `obj.status` do **laudo**) devem ser simplificados: como a trava
real agora é por linha e o inline não consegue expressar isso por linha,
o inline deixa de tentar bloquear via `has_delete_permission`/
`get_readonly_fields` (que só travariam tudo-ou-nada, o que voltaria a ser
o problema antigo) e passa a confiar inteiramente no erro de validação do
model quando a trava é violada.

**Sem mudança**: o que já existe no nível do `LaudoBaixa` (não do inline)
continua igual — `LaudoBaixaAdmin.has_delete_permission`/
`get_readonly_fields` (que travam o laudo inteiro quando o agregado é
`PROCESSADO`) e o bloqueio em `importar_itens_glpi` (que impede importar
itens novos num laudo 100% processado) não mudam, porque continuam
corretos com a nova semântica de agregado ("todos os itens processados").

## Fluxo da ação (`atualizar_status_itens_no_glpi`)

```
1. Validações de pré-condição (iguais a hoje):
   queryset.count() == 1, destinacao preenchida, laudo tem itens,
   todos os itens têm motivo_baixa, GLPIConfig + glpi_status_baixa_id
   configurados, GLPI_SESSION_UTILS_DISPONIVEL.

2. itens_a_processar = laudo.itens.exclude(status='PROCESSADO')
   Se itens_a_processar vazio → mensagem "Todos os itens já foram
   processados." (WARNING) e retorna — nada a fazer.

3. Se request.POST não tem o marcador de confirmação
   ('confirma_baixa_glpi'):
     → renderiza template de confirmação listando itens_a_processar
       (nome, tipo, patrimônio, status atual PENDENTE/FALHA + glpi_erro
       se houver) e o status ID alvo (config.glpi_status_baixa_id).
     → botão "Confirmar" reenvia POST com o marcador e os pks
       selecionados (hidden inputs, padrão do
       admin/delete_selected_confirmation.html).
     → botão "Cancelar" volta pro changelist sem tocar em nada.

4. Se confirmado: abre sessão legada (get_legacy_session_token),
   processa cada item de itens_a_processar:
     - ok → item.status='PROCESSADO', item.processado_em=now(),
       item.processado_por=request.user, item.glpi_erro='', save()
     - falha → item.status='FALHA', item.glpi_erro=error_msg, save()
   encerra sessão (finally: kill_legacy_session).

5. Recomputa laudo.status/data_baixa_glpi (ver seção acima).

6. Mensagem final:
   - todos os itens_a_processar deram certo → SUCCESS
   - alguns falharam → WARNING, citando quantos falharam (a lista de
     itens com FALHA fica visível na changelist / no laudo, via
     list_display do inline ou uma coluna de status)
```

### Template de confirmação

Novo arquivo `apps/reports/templates/admin/reports/laudobaixa/confirma_baixa_glpi.html`,
seguindo o padrão do `admin/delete_selected_confirmation.html` do Django
(estende `admin/base_site.html`, mesma estrutura de form com hidden
inputs + `{% csrf_token %}`). Fica dentro do app (`APP_DIRS=True` já
carrega isso, não precisa mexer em `TEMPLATES` no `settings.py`).

## UI / admin

- `ItemLaudoInline.fields` ganha uma coluna somente-leitura mostrando
  `status` (com `glpi_erro` como tooltip/segunda linha quando `FALHA`) —
  para o usuário ver, item a item, o que já foi processado e o que ainda
  falta, sem precisar abrir o laudo inteiro em outra tela.
- `LaudoBaixaAdmin.list_display`/`list_filter` continuam mostrando o
  `status` agregado do laudo (sem mudança).

## Erros e casos de borda

- **Sessão GLPI cai no meio do loop**: cada item é salvo individualmente
  assim que processado (não em lote no final), então itens já
  confirmados no GLPI antes da queda ficam `PROCESSADO` no Django mesmo
  que o restante do loop não rode. Reprocessar depois só pega o que
  sobrou.
- **`kill_legacy_session` falha**: já é best-effort hoje (captura exceção
  e segue); mantém esse comportamento.
- **Usuário reabre a tela de confirmação para um laudo cujo estado mudou
  entre o primeiro e o segundo POST** (ex.: outro usuário processou nesse
  meio tempo): o passo 2 (recalcular `itens_a_processar` a partir do
  banco, não da tela de confirmação) garante que só o que ainda está
  pendente/falho é reenviado — os pks vindos do form são só uma
  conveniência de UI, a query no passo 2 é sempre refeita no servidor
  antes de agir.

## Testes

Não há suíte de testes automatizados neste app hoje (`apps/reports` não
tem `tests.py`), então este trabalho segue o padrão do restante do app:
validação manual via Django admin local (rodar migration, criar laudo de
teste, rodar a ação com e sem falhas simuladas). Não introduzo uma suíte
nova como parte deste spec — é um esforço à parte, fora de escopo aqui.

## Fora de escopo (explicitamente adiado)

- Checkbox de exclusão por linha no inline (ver limitação técnica acima).
- Histórico completo de tentativas (log por evento) — decidido que o
  estado atual por item é suficiente por ora.
- Pré-checagem ao vivo do status atual no GLPI antes de mostrar a tela de
  confirmação.
