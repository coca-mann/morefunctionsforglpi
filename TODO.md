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

- [x] **7. Analisar e implementar django-unfold no admin**
  Concluído em 2026-08-20. Levantamento e plano de execução abaixo,
  mantidos como registro histórico.

  **Follow-up 2026-08-20: permissões no sidebar e em `/admin/reports/`.**
  O `SIDEBAR.navigation` criado não tinha nenhum `permission` callback —
  todo item aparecia pra qualquer staff, independente de ter permissão
  granular no model. Corrigido: cada item agora tem
  `"permission": lambda request: request.user.has_perm("<app>.view_<model>")`;
  grupos ficam automaticamente escondidos quando nenhum item deles é
  visível (comportamento nativo do template do Unfold, via CSS
  `has-[ol]:has-[li]:block`, não precisou de lógica extra). O item
  "Imprimir Etiquetas" ficou **sem** permission — a view
  `impressao_etiquetas_view` só checa `@staff_member_required`, sem
  permissão granular própria, então adicionar uma checagem só no sidebar
  criaria uma inconsistência (link escondido, URL ainda acessível
  direto). Se quiser isso mais estrito, precisa mexer na view também.

  Também corrigido um bug real em `/admin/reports/`: `LaudoTecnicoAdmin`
  (o model fake que segura a rota) tinha `has_module_permission` sempre
  `True`, liberando a página pra qualquer staff. Trocado pra
  `request.user.has_module_perms('reports')`. Isso sozinho não bastava —
  o Django também exige que o próprio `LaudoTecnico` passe em
  `get_model_perms()`, que por padrão checa a permissão específica dele
  (`view_laudotecnico`, que ninguém tem), e sem isso a página voltava a
  dar 404 mesmo pra quem tinha permissão nos models reais. Corrigido
  sobrescrevendo `has_view_permission` do mesmo jeito. `app_index.html`
  também ganhou `{% if perms.reports.view_xxx %}` em cada card. Validado
  com um usuário de teste descartável (criado e removido na mesma
  sessão): sem permissão → 404 na rota e sidebar só com "Dashboard"; com
  só `view_laudobaixa` → 200, só o card/link de Laudos de Baixa aparece.

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

  **Fase A — Atualizar pacotes do ecossistema Django antes do Unfold ([x] concluída em 2026-08-20, commit `fbcca79`)**
  (pedido explícito do usuário, feito nesta ordem por causa do próximo
  passo). Levantado via `pip-review --local` em 2026-08-20:
  - `Django` 6.0.1 → 6.1 (estável, mesma major — checar notas de
    depreciação antes de trocar)
  - `djangorestframework` 3.16.1 → 3.18.0
  - `django-allauth` — **achado à parte**: estava no `requirements.txt`
    mas não era usada em lugar nenhum (não estava em `INSTALLED_APPS`,
    não era importada por nenhum app). Removida (commit seguinte).
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
  - Achado durante o `manage.py check`/leitura das release notes do 6.1:
    `LaudoBaixaAdmin.get_actions()` (`apps/reports/admin.py:233`) está no
    formato antigo (sem `action_location`) — deprecated no 6.1, ainda
    funciona mas gera warning; remoção definitiva prevista pro Django
    7.0. Não bloqueia nada agora, ajustar numa limpeza futura.

  **Fase B — Instalar e configurar o `django-unfold` ([x] concluída em
  2026-08-20, commit `e7731ad`, confirmação visual feita pelo usuário)**
  - `django-unfold==0.104.1` instalado, `'unfold'` em `INSTALLED_APPS`
    antes de `django.contrib.admin`, dict `UNFOLD` em `core/settings.py`.
  - Achado durante a instalação: a doc do Unfold exige que todo
    `ModelAdmin`/`TabularInline` herde das classes do `unfold.admin`, não
    das do `django.contrib.admin` — "usar o `ModelAdmin` padrão do Django
    resulta em formulários sem estilo e funcionalidade quebrada". Trocada
    a base de las 16 classes registradas (`dbcom`: 4, `panel`: 2,
    `printer`: 2, `reports`: 8; `glpiintegrator` não tem nenhuma).

  **Fase B.1 — Sidebar customizado (commit `e1f9282`)**
  - `UNFOLD["SITE_HEADER"]` = "Mais Funções do GLPI"; `SIDEBAR.navigation`
    definido explicitamente, substituindo o menu automático por-app do
    Unfold por grupos: Início, Integração GLPI, Painel NOC, Impressão de
    Etiquetas, Laudos e Protocolos, Administração.
  - Cada item linka direto pra URL real do model (`admin:<app>_<model>_changelist`)
    via `reverse_lazy`, inclusive os models "escondidos"
    (`has_module_permission=False`: `LaudoBaixa`, `MotivoBaixa`,
    `ProtocoloReparo`, `ConfiguracaoCabecalho`) — isso contorna
    completamente o workaround antigo de proxy models
    (`LaudoTecnicoAdmin`/`ProtocoloReparoProxyAdmin`) que existia só pra
    criar um ponto de entrada clicável na página clássica `app_index` do
    Django. Ver observação sobre `app_index.html` na Fase C abaixo.

  **Fase C — Adaptar as templates customizadas ([x] 5 de 6 concluídas,
  commits `f1e88a5`, `aa2a1b0`, `5ffa809`, `3ce5c6b` e um commit não
  identificado por hash aqui para `dbcom/externaldbconfig/change_form.html`)**
  1. [x] `templates/admin/index.html` — card de atalho próprio (não usou
     `DASHBOARD_CALLBACK` da doc oficial, mais simples pra esse caso: só
     um link a mais no dashboard, não um dashboard novo)
  2. [x] `templates/admin/reports/app_index.html` — recriado do zero,
     estilo Unfold (cards com link direto pra `LaudoBaixa`,
     `MotivoBaixa`, `ProtocoloReparo`, `ConfiguracaoCabecalho`).
     **Histórico**: a versão original foi removida junto com
     `LaudoTecnicoAdmin`/`ProtocoloReparoProxyAdmin` (que existiam só
     pra dar um ponto de entrada clicável nele) por parecer código
     morto — só que sem NENHUM model com `has_module_permission=True`
     no app `reports`, a própria rota `/admin/reports/` passou a dar
     404 (view `app_index` do Django exige pelo menos um). Corrigido
     restaurando um `LaudoTecnicoAdmin` mínimo (só
     `has_module_permission=True`, sem o redirect de antes) pra
     destravar a rota, com o template novo fazendo o trabalho de
     verdade. `ProtocoloReparoProxyAdmin` não foi restaurado — não é
     necessário, um model já basta. Os models proxy `LaudoTecnico`/
     `ProtocoloReparoProxy` continuam existindo em `models.py`.
  3. [x] `templates/admin/impressao_etiquetas.html` — paleta própria +
     `var(--color-primary-500)` do Unfold pro destaque; atalho no sidebar
     e no dashboard
  4. [x] `etiquetalayout/change_form.html` + `layout_editor.css` —
     botões do editor (`.le-btn`), borda de seleção do elemento, fundo do
     container
  5. [x] `printserver/change_form.html` + `print_server_admin.css` —
     campo "Chave de API" trocado pro `UnfoldAdminPasswordToggleWidget`
     nativo do Unfold (não CSS manual); seção "Ações do Servidor Remoto"
     reconstruída como card próprio (o `fieldset.module.aligned`/`form-row`
     clássico não tem mais CSS correspondente no Unfold)
  6. [x] `dbcom/externaldbconfig/change_form.html` — mesmo tratamento:
     botão "Testar Conexão" e o resultado do teste (sucesso/erro) via
     classes CSS em vez de cor fixa no JS; campo de senha do
     `ExternalDbConfigForm` também trocado pro `UnfoldAdminPasswordToggleWidget`

  **Fase D — Validar comportamento ([x] concluída, via teste automatizado
  com `Client` + `force_login`, já que a extensão do Chrome não conectou
  nesta sessão)**:
  - [x] Singletons (`GLPIConfig`, `DashboardSettings`,
    `ConfiguracaoCabecalho`) — redirecionamento changelist→change, 302
    confirmado nos três
  - [x] Travas de edição/exclusão por status — `ProtocoloReparo`
    `FINALIZADO` renderiza a página de change sem erro (fluxo de
    `get_fieldsets`/`get_form`/`get_readonly_fields` intacto)
  - [x] Ações customizadas — `get_actions()` continuam registradas
    (achado à parte já anotado na Fase A: `LaudoBaixaAdmin.get_actions()`
    está no formato deprecated do Django 6.1, não relacionado ao Unfold)
  - [x] CSP do iframe do GLPI — **achado e corrigido, bug pré-existente
    não relacionado ao Unfold**: `AllowAdminInIframeMiddleware` (que
    deveria remover o `X-Frame-Options`) estava listado ANTES de
    `django.middleware.clickjacking.XFrameOptionsMiddleware` no
    `MIDDLEWARE` (`core/settings.py`). Como a ordem de `process_response`
    é inversa à da lista, o `XFrameOptionsMiddleware` rodava DEPOIS e
    recolocava `X-Frame-Options: DENY` já que o header tinha acabado de
    sumir — confirmado via teste antes da correção. Corrigido invertendo
    a ordem dos dois na lista; reconfirmado via teste que o header some
    de verdade e o `Content-Security-Policy: frame-ancestors` continua
    presente.

  **Fase E — testar no navegador ([x] concluída pelo usuário**, tela por
  tela, ao longo da implementação — a extensão do Chrome não conectou
  nesta sessão então a IA não conseguiu verificar visualmente por conta
  própria em nenhum momento, só via `curl`/test client).

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
