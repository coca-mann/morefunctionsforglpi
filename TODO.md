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
  Avaliar compatibilidade com Django 6.0.1 e com as customizações já
  existentes no admin deste projeto (templates de confirmação de action,
  singletons, inlines, CSP para iframe do GLPI) antes de instalar.

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
