# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

> Nota: este changelog passa a ser mantido a partir da versão `0.1.0`.
> Versões anteriores (se houver) não foram reconstruídas retroativamente;
> consulte o histórico de PRs no Git caso precise dessa informação.

## [Unreleased]

### Added

- [e7731ad](https://github.com/coca-mann/morefunctionsforglpi/commit/e7731ad), [e1f9282](https://github.com/coca-mann/morefunctionsforglpi/commit/e1f9282), [f1e88a5](https://github.com/coca-mann/morefunctionsforglpi/commit/f1e88a5), [aa2a1b0](https://github.com/coca-mann/morefunctionsforglpi/commit/aa2a1b0), [5ffa809](https://github.com/coca-mann/morefunctionsforglpi/commit/5ffa809), [3ce5c6b](https://github.com/coca-mann/morefunctionsforglpi/commit/3ce5c6b), [d26e8d3](https://github.com/coca-mann/morefunctionsforglpi/commit/d26e8d3), [28b2463](https://github.com/coca-mann/morefunctionsforglpi/commit/28b2463) - Substitui o tema padrão do Django admin pelo `django-unfold`: sidebar reorganizado por seção com ícones, dashboard e as telas com customização própria (impressão de etiquetas, editor de layout de etiqueta, configuração de servidor de impressão, configuração de banco externo) adaptadas para o novo tema, incluindo widgets nativos de senha e dropdown

### Changed

- [fbcca79](https://github.com/coca-mann/morefunctionsforglpi/commit/fbcca79), [d4590d6](https://github.com/coca-mann/morefunctionsforglpi/commit/d4590d6) - Atualiza Django (6.0.1 → 6.1) e Django REST Framework (3.16.1 → 3.18.0); remove a dependência `django-allauth`, que não era utilizada em nenhum lugar do código

### Fixed

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
