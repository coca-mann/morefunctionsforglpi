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

## [0.1.1] - 2026-08-20

### Changed

- [ef4dd4d](https://github.com/coca-mann/morefunctionsforglpi/commit/ef4dd4d) - Passa a versionar os arquivos de migration do Django (antes fora do controle de versão); ambientes com histórico de migration divergente e já aplicado devem reconciliar via `migrate <app> --fake`

## [0.1.0] - 2026-08-20

### Added

- [ffa7365](https://github.com/coca-mann/morefunctionsforglpi/commit/ffa7365) - Adiciona guia de arquitetura do projeto (`CLAUDE.md`)
- [5e6356b](https://github.com/coca-mann/morefunctionsforglpi/commit/5e6356b) - Adiciona infraestrutura de changelog e template de Pull Request (`CHANGELOG.md`, `docs/versioning.md`, `.github/PULL_REQUEST_TEMPLATE.md`)
- [a923666, a6c0ae1](https://github.com/coca-mann/morefunctionsforglpi/commit/a923666) - Realiza auditoria completa de código e mapeamento de funcionalidades do projeto (relatórios mantidos localmente, não versionados por conterem detalhes sensíveis)
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
