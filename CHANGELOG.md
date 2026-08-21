# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

> Nota: este changelog passa a ser mantido a partir da versão `0.1.0`.
> Versões anteriores (se houver) não foram reconstruídas retroativamente;
> consulte o histórico de PRs no Git caso precise dessa informação.

## [Unreleased]

### Added

### Changed

### Fixed

### Security

## [0.5.1] - 2026-08-21

### Security

- [674760d](https://github.com/coca-mann/morefunctionsforglpi/commit/674760d) - Corrige o parsing de `DEBUG`: qualquer valor não vazio (inclusive a string `'False'`) era tratado como `True`, então `DEBUG` podia continuar ativo em produção mesmo com a variável de ambiente configurada para desligá-lo
- [ee71076](https://github.com/coca-mann/morefunctionsforglpi/commit/ee71076) - Superusuário padrão criado no postinstall passa a ter senha aleatória por instalação em vez da senha fixa `password`, que deixava qualquer instalação esquecida acessível indefinidamente com a mesma credencial
- [3e97456](https://github.com/coca-mann/morefunctionsforglpi/commit/3e97456) - Corrige dois problemas no login via SSO do GLPI: o parâmetro `next` (fora do payload assinado) permitia redirecionar a vítima para qualquer URL após o login, e a busca de usuário por e-mail podia logar a pessoa numa conta local já existente sem checar posse do e-mail; identidade agora é resolvida só por `glpi_id`, e o redirect é validado contra o host atual
- [3bd70d7](https://github.com/coca-mann/morefunctionsforglpi/commit/3bd70d7) - Middleware que libera o embed do admin em iframe passa a agir só em `/admin/`; antes relaxava a proteção contra clickjacking (CSP `frame-ancestors` e remoção do `X-Frame-Options`) em toda resposta do site, incluindo o painel NOC e as APIs do printer/reports
- [afc235e](https://github.com/coca-mann/morefunctionsforglpi/commit/afc235e) - Endpoint de webhook do GLPI volta a validar a assinatura HMAC da chamada; estava desligado de propósito, então qualquer um que descobrisse a URL do webhook conseguia disparar mudanças reais de status de ativos no GLPI
- [fa1ee59](https://github.com/coca-mann/morefunctionsforglpi/commit/fa1ee59) - Remove os `print()` que vazavam os headers completos (App-Token, Session-Token, Authorization) da API legada do GLPI em texto puro no log do servidor a cada chamada
- [32f98ee](https://github.com/coca-mann/morefunctionsforglpi/commit/32f98ee) - As três views que geram PDF de laudos/protocolos passam a exigir autenticação de staff; antes qualquer um que adivinhasse um ID baixava o documento sem login
- [d4e0945](https://github.com/coca-mann/morefunctionsforglpi/commit/d4e0945) - Escapa o texto das etiquetas antes de montar o PDF: um nome de ativo com `&`, `<` ou `>` (ex.: "R&D") era interpretado como XML pelo ReportLab e derrubava a impressão com exceção não tratada
- [6d7ee1c](https://github.com/coca-mann/morefunctionsforglpi/commit/6d7ee1c) - WebSocket do painel (`ws/panel/`) passa a exigir um token de controle para reassumir o canal de um display já identificado; antes, qualquer conexão anônima podia mandar o `clientId` de um kiosk existente e sequestrar os comandos de controle remoto (troca de tela) destinados a ele — a leitura de dados (tickets/KPIs) continua aberta, sem exigir o token

## [0.5.0] - 2026-08-21

### Added

- [cd5ac9e](https://github.com/coca-mann/morefunctionsforglpi/commit/cd5ac9e) - A ação de aplicar a baixa no GLPI passa a usar a API REST v2.3 (OAuth2, conta de serviço) em vez da API legada v1, com PATCH direto por item e suporte tanto a ativos nativos quanto a Custom Assets (endpoint e campo de status próprios para cada caso)

### Fixed

- [0c6a98d](https://github.com/coca-mann/morefunctionsforglpi/commit/0c6a98d) - Corrige a migration `0009` do app `reports` (rename dos campos de `ItemLaudo`), que só funcionava no ambiente onde tinha sido criada; em qualquer outro ambiente limpo o `migrate` falhava com "Unknown column"
- [b6f820a](https://github.com/coca-mann/morefunctionsforglpi/commit/b6f820a) - Corrige a estilização da tela de confirmação de baixa e do modal "Ver log" do Laudo de Baixa (sem estilo sob o tema `django-unfold`), a centralização e animação do modal, e o botão "Fechar" que estava voltando para a lista de laudos em vez de só fechar o modal
- [1fe86c3](https://github.com/coca-mann/morefunctionsforglpi/commit/1fe86c3) - Esconde os botões de Salvar do Laudo de Baixa quando ele já está processado no GLPI, e o checkbox de remoção dos itens já processados na lista de itens do laudo
- [b142931](https://github.com/coca-mann/morefunctionsforglpi/commit/b142931) - Desabilita a seleção de Laudos de Baixa já processados na lista do admin, inclusive via "selecionar todos", para que não sejam escolhidos por engano para rodar uma ação

## [0.4.0] - 2026-08-21

### Added

- [24622da](https://github.com/coca-mann/morefunctionsforglpi/commit/24622da) - Laudo de Baixa passa a exigir confirmação antes de escrever no GLPI (tela intermediária listando os itens pendentes/com falha e o status alvo) e registra quem processou cada item; a trava de edição/exclusão agora é por item, não mais pelo agregado do laudo inteiro

### Fixed

- [bf61fec](https://github.com/coca-mann/morefunctionsforglpi/commit/bf61fec) - Corrige a descoberta de testes automatizados (`manage.py test`) para qualquer app do projeto: `apps/` estava sem `__init__.py`, o que quebrava a descoberta de testes do unittest para qualquer app_label no formato `apps.<nome>`

## [0.3.0] - 2026-08-21

### Added

- [471ae43](https://github.com/coca-mann/morefunctionsforglpi/commit/471ae43) - Laudo de Baixa passa a registrar o status de processamento (pendente/processado/erro) e o log de sucesso ou erro do GLPI para cada item; reexecutar a ação após uma falha parcial reprocessa só os itens ainda pendentes

### Changed

- [092789f](https://github.com/coca-mann/morefunctionsforglpi/commit/092789f) - Remove os templates de login do `django-allauth` (`templates/account/login.html`, `templates/socialaccount/login.html`), órfãos desde a remoção da dependência

## [0.2.0] - 2026-08-21

### Added

- [e7731ad](https://github.com/coca-mann/morefunctionsforglpi/commit/e7731ad), [e1f9282](https://github.com/coca-mann/morefunctionsforglpi/commit/e1f9282), [f1e88a5](https://github.com/coca-mann/morefunctionsforglpi/commit/f1e88a5), [aa2a1b0](https://github.com/coca-mann/morefunctionsforglpi/commit/aa2a1b0), [5ffa809](https://github.com/coca-mann/morefunctionsforglpi/commit/5ffa809), [3ce5c6b](https://github.com/coca-mann/morefunctionsforglpi/commit/3ce5c6b), [d26e8d3](https://github.com/coca-mann/morefunctionsforglpi/commit/d26e8d3), [28b2463](https://github.com/coca-mann/morefunctionsforglpi/commit/28b2463) - Substitui o tema padrão do Django admin pelo `django-unfold`: sidebar reorganizado por seção com ícones, dashboard e as telas com customização própria (impressão de etiquetas, editor de layout de etiqueta, configuração de servidor de impressão, configuração de banco externo) adaptadas para o novo tema, incluindo widgets nativos de senha e dropdown

### Changed

- [fbcca79](https://github.com/coca-mann/morefunctionsforglpi/commit/fbcca79), [d4590d6](https://github.com/coca-mann/morefunctionsforglpi/commit/d4590d6) - Atualiza Django (6.0.1 → 6.1) e Django REST Framework (3.16.1 → 3.18.0); remove a dependência `django-allauth`, que não era utilizada em nenhum lugar do código

### Security

- [32beb93](https://github.com/coca-mann/morefunctionsforglpi/commit/32beb93), [a673c0a](https://github.com/coca-mann/morefunctionsforglpi/commit/a673c0a) - Sidebar e a página de índice do app de laudos (`/admin/reports/`) passam a respeitar as permissões granulares do Django em vez de aparecer pra qualquer usuário staff
- [7582bca](https://github.com/coca-mann/morefunctionsforglpi/commit/7582bca) - Corrige a ordem dos middlewares que impedia a remoção efetiva do header `X-Frame-Options`, quebrando o embed do admin no iframe do GLPI

## [0.1.1] - 2026-08-20

### Changed

- [ef4dd4d](https://github.com/coca-mann/morefunctionsforglpi/commit/ef4dd4d) - Passa a versionar os arquivos de migration do Django (antes fora do controle de versão); ambientes com histórico de migration divergente e já aplicado devem reconciliar via `migrate <app> --fake`

## [0.1.0] - 2026-08-20

### Added

- [ffa7365](https://github.com/coca-mann/morefunctionsforglpi/commit/ffa7365) - Adiciona guia de arquitetura do projeto (`CLAUDE.md`)
- [5e6356b](https://github.com/coca-mann/morefunctionsforglpi/commit/5e6356b) - Adiciona infraestrutura de changelog e template de Pull Request (`CHANGELOG.md`, `docs/versioning.md`, `.github/PULL_REQUEST_TEMPLATE.md`)
- [a923666](https://github.com/coca-mann/morefunctionsforglpi/commit/a923666), [a6c0ae1](https://github.com/coca-mann/morefunctionsforglpi/commit/a6c0ae1) - Realiza auditoria completa de código e mapeamento de funcionalidades do projeto (relatórios mantidos localmente, não versionados por conterem detalhes sensíveis)
- [c430075](https://github.com/coca-mann/morefunctionsforglpi/commit/c430075) - Adiciona `README.md` do projeto

### Security

- [9544674](https://github.com/coca-mann/morefunctionsforglpi/commit/9544674) - Remove do controle de versão os relatórios de auditoria com detalhes de exploração, por serem incompatíveis com repositório público

<!--
Ao criar uma nova tag:
1. Renomeie a seção acima para incluir a versão:
   ## [Unreleased]

   ## [X.Y.Z] - AAAA-MM-DD
   ### Added
   - ...
2. Copie o conteúdo da seção "Changelog" do(s) MR(s)/PR(s) incluídos na tag.
3. Preencha a data no formato AAAA-MM-DD.
-->
