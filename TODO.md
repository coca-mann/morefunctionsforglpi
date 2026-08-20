# TODO

Lista de trabalho em andamento, criada em 2026-08-20. Itens marcados `[ ]`
ainda não começaram; `[~]` em andamento; `[x]` concluído.

## Ordem de execução

O item 1 é bloqueante dos demais: nenhum outro trabalho deste TODO deve
ser commitado direto na `main` — tudo passa a acontecer na branch `dev`
a partir daqui.

## Itens

- [x] **1. Criar branch `dev` e passar a trabalhar somente nela**
  A partir deste ponto, nada deste TODO é commitado direto na `main`.

- [x] **2. Análise completa do código: erros e redundâncias**
  Relatório com múltiplos achados de severidade alta, boa parte segurança
  real. **Mantido só localmente** (`docs/code-review-2026-08-20.md`,
  gitignored — não versionado porque este repositório é público e o
  relatório contém detalhes de exploração). Nada foi corrigido ainda —
  próximo passo é decidir prioridade e corrigir.

- [x] **3. Documentar todas as funcionalidades disponíveis**
  Catálogo completo, incluindo cruzamento com o audit de segurança que
  achou vários achados novos ao mapear as funcionalidades. **Mantido só
  localmente** (`docs/features.md`, gitignored, mesmo motivo do item 2).

- [x] **4. Resolver migrations fora do `.gitignore` sem quebrar produção**
  `migrations/` tirado do `.gitignore`; arquivos do dev local adotados
  como histórico canônico e versionados (commit `ef4dd4d`, PR #2). Cada
  ambiente já implantado tinha gerado seu próprio histórico de migration
  divergente (nomes/fatiamento diferentes, mesmo schema final — confirmado
  via `makemigrations --check --dry-run` limpo em cada um). Reconciliado
  no servidor de testes doméstico via `migrate <app> --fake` por app, após
  remover os arquivos órfãos não-rastreados que coexistiam com os
  canônicos pós-`git pull` (`dbcom`/`reports` tinham 1 cada). `glpiintegrator`
  é um caso à parte: a pasta de migrations tinha sumido de vez (schema
  intacto no banco, provável `git clean` em algum momento) — reconciliado
  do mesmo jeito. **Falta repetir este procedimento na produção real da
  empresa quando ela for atualizada** — não assumir que é igual ao servidor
  de testes, refazer o levantamento (`showmigrations` + `makemigrations
  --check`) lá antes de decidir fake vs. migrate real.

- [x] **5. Criar infraestrutura de changelog e Pull Request**
  `CHANGELOG.md` e `docs/versioning.md` preenchidos; comandos globais
  `/changelog-pr` e `/changelog-release` (`gh`, não `glab` — este repo é
  GitHub) em `~/.claude/commands/`.

- [x] **6. Criar template de Pull Request para o GitHub**
  `.github/PULL_REQUEST_TEMPLATE.md`, alinhado ao fluxo definido no item 5.

- [ ] **7. Analisar e implementar django-unfold no admin**
  Levantamento feito em 2026-08-20. **Ainda não implementado — plano
  registrado abaixo, aguardando execução.**

  Compatibilidade: sem bloqueio. `django-unfold` 0.104.1 (mais recente)
  declara suporte oficial a Django 5.2/6.0/6.1 e exige Python ≥3.12; o venv
  já está em 3.12.6.

  Achado principal: o admin deste projeto tem bastante customização de
  template, não é um admin "de fábrica". 6 templates custom identificados,
  todos estendendo templates padrão do Django (`admin/change_form.html`,
  `admin/base_site.html`, `admin/index.html`):
  - `templates/admin/index.html` — dashboard customizada da home
  - `templates/admin/reports/app_index.html` — índice do app `reports`
    com links manuais pros singletons
  - `templates/admin/impressao_etiquetas.html` (445 linhas)
  - `apps/printer/.../etiquetalayout/change_form.html` — editor visual
    (JS externo via CDN, `interactjs`)
  - `apps/printer/.../printserver/change_form.html` — botões JS de busca
    de impressora do Windows
  - `templates/admin/dbcom/externaldbconfig/change_form.html` — botão de
    teste de conexão MySQL via AJAX

  A doc oficial do Unfold confirma que o dashboard **não é** um drop-in
  1:1: o padrão recomendado é `templates/admin/index.html` estendendo
  `admin/base.html` (dele) + `DASHBOARD_CALLBACK`, diferente do que já
  existe aqui hoje (estende `admin/index.html` padrão do Django). Para os
  `change_form.html` com blocos (`field_sets`, `content`,
  `submit_buttons_bottom`, `admin_change_form_document_ready`) não há
  confirmação na doc de que os nomes de bloco continuam idênticos — precisa
  verificar na prática, tela por tela.

  ### Plano de execução

  **Fase A — Atualizar pacotes do ecossistema Django antes do Unfold**
  (pedido explícito do usuário, feito nesta ordem por causa do próximo
  passo). Levantado via `pip-review --local` em 2026-08-20:
  - `Django` 6.0.1 → 6.1 (estável, mesma major — checar notas de
    depreciação antes de trocar)
  - `djangorestframework` 3.16.1 → 3.18.0
  - `django-allauth` 65.14.0 → 65.19.1 — **achado à parte**: esta
    dependência está no `requirements.txt` mas não é usada em lugar
    nenhum (não está em `INSTALLED_APPS`, não é importada por nenhum
    app). Decidir se atualiza mesmo assim ou remove — não bloqueia o
    Unfold.
  - `django-cors-headers`, `djangorestframework_simplejwt`, `channels`,
    `channels_redis`: já na versão mais recente, nada a fazer.
  - Depois do bump: `python manage.py check` + teste manual dos fluxos
    principais (dashboard websocket, login no admin, endpoints JWT do
    `printer`, SSO do `glpiintegrator`) antes de seguir pra Fase B.
  - Fora do escopo (não relacionados a Django/admin, cada um merece
    avaliação própria depois): `reportlab` 4→5 (major, afeta geração de
    PDF dos laudos), `mysql-connector-python`, `cryptography`,
    `pyinstaller` e demais pacotes fora do ecossistema Django que também
    apareceram desatualizados no `pip-review`.

  **Fase B — Instalar e configurar o `django-unfold`**
  - `pip install django-unfold==0.104.1` (reconferir compatibilidade com
    o Django 6.1 já atualizado antes de fixar a versão)
  - Adicionar `'unfold'` (e módulos `unfold.contrib.*` que forem
    necessários) em `INSTALLED_APPS`, **antes** de `django.contrib.admin`
  - Configurar o dict `UNFOLD` em `core/settings.py` (título, cores,
    sidebar)

  **Fase C — Adaptar as 6 templates customizadas, uma por vez, testando
  no navegador antes de ir pra próxima** (não migrar tudo de uma vez):
  1. `templates/admin/index.html` — reescrever pro padrão do Unfold
     (`admin/base.html` + `DASHBOARD_CALLBACK`)
  2. `templates/admin/reports/app_index.html` — provavelmente precisa
     virar algo dentro do novo paradigma de sidebar do Unfold, não mais
     um "app_index" clássico
  3. `templates/admin/impressao_etiquetas.html`
  4. `etiquetalayout/change_form.html` (+ JS externo `interactjs`)
  5. `printserver/change_form.html`
  6. `dbcom/externaldbconfig/change_form.html`

  **Fase D — Validar comportamento (não é visual, mas pode ser afetado
  por mudança de template base)**:
  - Singletons (`GLPIConfig`, `DashboardSettings`, `ConfiguracaoCabecalho`)
    — redirecionamento changelist→change
  - Travas de edição/exclusão por status (`LaudoBaixa`/`ItemLaudo`
    `PROCESSADO`; `ProtocoloReparo`/`ItemReparo` `FINALIZADO`)
  - Ações customizadas (`importar_itens_glpi`,
    `atualizar_status_itens_no_glpi`, `importar_chamados_glpi`)
  - CSP do iframe do GLPI (`AllowAdminInIframeMiddleware`) continua
    liberando os assets estáticos do Unfold dentro do iframe

  **Fase E** — testar cada tela no navegador (dev server) antes de
  declarar a tarefa concluída — não presumir pela documentação.

- [x] **9. Criar README para o projeto**
  `README.md` criado na raiz — funcionalidades, quick start de dev,
  frontend Vue, build do executável standalone, versionamento.

- [ ] **8. Migrar integração GLPI para API v2.3 com OAuth**
  Hoje as escritas no GLPI (`apps/dbcom/utils.py`) usam a API legada v1
  (initSession/killSession com App-Token + User-Token). Converter para a
  API v2.3, que usa OAuth. Decidir também se as leituras diretas via SQL
  (`apps/dbcom/glpi_queries.py`) continuam bypassando a API ou migram
  junto — `GLPIConfig.glpi_api_url` já aponta pra um path `/v2` mesmo com
  o fluxo de sessão ainda sendo v1, então há inconsistência a resolver
  aqui também. Interessa às tasks #1 (achados de segurança em
  `dbcom/views.py`/`utils.py`) e à confirmação HMAC do webhook.

## Spec pausada (não faz parte deste TODO)

`docs/superpowers/specs/2026-08-20-baixa-patrimonial-item-tracking-design.md`
e seu plano em `docs/superpowers/plans/2026-08-20-baixa-patrimonial-item-tracking.md`
ficam parados até o usuário retomar — não iniciar implementação sem pedido
explícito.
