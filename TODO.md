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

- [ ] **3. Documentar todas as funcionalidades disponíveis**
  Mapear o que cada app faz hoje, como referência funcional do sistema.

- [ ] **4. Resolver migrations fora do `.gitignore` sem quebrar produção**
  Hoje `migrations/` está no `.gitignore` de cada app, forçando
  `makemigrations`/estado não versionado direto em produção.
  **Risco a investigar antes de mexer em código**: produção já roda com
  um schema aplicado sem histórico de migration versionado no repo — se
  as migrations que existem localmente não baterem exatamente com o
  schema real de produção, o próximo `migrate` em prod pode tentar
  aplicar operações redundantes ou conflitantes. Precisa de um
  levantamento do schema real de produção (`mysqldump --no-data` ou
  equivalente) comparado ao que as migrations locais gerariam, antes de
  decidir a estratégia (ex: `--fake-initial`, squashing, ou recriar o
  histórico de migrations do zero por app).

- [x] **5. Criar infraestrutura de changelog e Pull Request**
  `CHANGELOG.md` e `docs/versioning.md` preenchidos; comandos globais
  `/changelog-pr` e `/changelog-release` (`gh`, não `glab` — este repo é
  GitHub) em `~/.claude/commands/`.

- [x] **6. Criar template de Pull Request para o GitHub**
  `.github/PULL_REQUEST_TEMPLATE.md`, alinhado ao fluxo definido no item 5.

- [ ] **7. Analisar e implementar django-unfold no admin**
  Avaliar compatibilidade com Django 6.0.1 e com as customizações já
  existentes no admin deste projeto (templates de confirmação de action,
  singletons, inlines, CSP para iframe do GLPI) antes de instalar.

- [ ] **9. Criar README para o projeto**
  Não existe `README.md` na raiz. Cobrir o que o projeto é, como rodar em
  dev, como buildar o executável standalone, e um resumo de arquitetura
  (pode reaproveitar boa parte do `CLAUDE.md`).

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
