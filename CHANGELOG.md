# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

> Nota: este changelog passa a ser mantido a partir da versão `0.1.0`.
> Versões anteriores (se houver) não foram reconstruídas retroativamente;
> consulte o histórico de PRs no Git caso precise dessa informação.

## [Unreleased]

### Added

- [cd5ac9e](https://github.com/coca-mann/morefunctionsforglpi/commit/cd5ac9e) - A ação de aplicar a baixa no GLPI passa a usar a API REST v2.3 (OAuth2, conta de serviço) em vez da API legada v1, com PATCH direto por item e suporte tanto a ativos nativos quanto a Custom Assets (endpoint e campo de status próprios para cada caso)

### Changed

### Fixed

- [0c6a98d](https://github.com/coca-mann/morefunctionsforglpi/commit/0c6a98d) - Corrige a migration `0009` do app `reports` (rename dos campos de `ItemLaudo`), que só funcionava no ambiente onde tinha sido criada; em qualquer outro ambiente limpo o `migrate` falhava com "Unknown column"
- [b6f820a](https://github.com/coca-mann/morefunctionsforglpi/commit/b6f820a) - Corrige a estilização da tela de confirmação de baixa e do modal "Ver log" do Laudo de Baixa (sem estilo sob o tema `django-unfold`), a centralização e animação do modal, e o botão "Fechar" que estava voltando para a lista de laudos em vez de só fechar o modal
- [1fe86c3](https://github.com/coca-mann/morefunctionsforglpi/commit/1fe86c3) - Esconde os botões de Salvar do Laudo de Baixa quando ele já está processado no GLPI, e o checkbox de remoção dos itens já processados na lista de itens do laudo
- [b142931](https://github.com/coca-mann/morefunctionsforglpi/commit/b142931) - Desabilita a seleção de Laudos de Baixa já processados na lista do admin, inclusive via "selecionar todos", para que não sejam escolhidos por engano para rodar uma ação

### Security

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
