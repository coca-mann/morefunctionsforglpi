# Versionamento e Changelog

> Template reutilizável. Colocar em `docs/versioning.md` no repositório.
> Antes de usar num projeto novo, preencha a seção "Adaptação" abaixo — o
> resto do documento depende dessas respostas.

## Adaptação para este projeto (preenchido em 2026-08-20)

- **Consumidor(es) externo(s) deste projeto:** nenhum. É uma aplicação
  standalone: o Django admin (embutido via iframe no GLPI,
  `apps.glpiintegrator.middleware.AllowAdminInIframeMiddleware`) e o painel
  Vue (`apps/panel/frontend/vue`) são partes do mesmo projeto/deploy, não
  consumidores externos com ciclo de vida independente.
- **Existe deploy conjunto/simultâneo entre este projeto e o consumidor?**
  Não aplicável (sem consumidor externo).
- **Plataforma de repositório:** GitHub
  (`https://github.com/coca-mann/morefunctionsforglpi`).
- **Idioma do changelog e dos PRs:** Português.
- **Idioma dos commits:** Inglês (convenção já usada pelo comando `/commit`
  deste projeto — título/descrição em inglês, conventional commits).

Como não há consumidor externo, o critério de MAJOR abaixo usa o critério
clássico de semver: mudança que quebra compatibilidade para qualquer usuário
direto do software (não "contrato de API" consumido por terceiros).

## Esquema

Seguimos [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

## Critérios de bump

### PATCH
Correção de comportamento que **não altera** nada que o(s) consumidor(es)
externo(s) definido(s) acima já consomem hoje: formato de resposta, endpoint,
nome/tipo de campo, código de status, comportamento de autenticação.

### MINOR
Funcionalidade nova, **aditiva**, que não altera nem remove nada que já
existe. O consumidor atual continua funcionando sem nenhuma mudança, mesmo
sem consumir a novidade.

### MAJOR
**Qualquer alteração em algo que o consumidor externo já usa hoje** —
independente do tamanho da mudança. O critério não é "quanto a estrutura
interna mudou", é "o contrato externo mudou". Isso inclui:

- Renomear, remover ou mudar o tipo de um campo já retornado.
- Mudar o formato de uma resposta.
- Mudar um código de status já utilizado.
- Alterar comportamento de autenticação/autorização existente.
- Remover ou renomear um endpoint/função pública.

Um refactor grande que não altera nenhum contrato externo **não é** MAJOR —
é, no máximo, `Changed` interno, registrado no changelog sem forçar bump
maior que patch/minor.

### Exceção: desenvolvimento e deploy conjunto com o consumidor

Se este projeto e seu(s) consumidor(es) são desenvolvidos e deployados
**simultaneamente** (sem janela de dessincronia em produção), uma mudança de
contrato pode subir como MINOR ou PATCH. Mesmo assim, registre a mudança no
changelog na categoria `Changed` (ou `Removed`), com nota explícita de que o
contrato mudou e o consumidor foi atualizado junto.

Se essa exceção não se aplica ao seu projeto (consumidor com ciclo de deploy
independente, ou múltiplos consumidores fora do seu controle), remova esta
seção — ela não deve ser usada como desculpa padrão para evitar bump MAJOR.

## Quem decide

A análise do diff/MR para determinar o tipo de bump e gerar a entrada de
changelog é feita pelo Claude Code, seguindo estritamente os critérios acima
(ver configuração em `CLAUDE.md`). Em caso de dúvida entre duas categorias, o
Claude Code deve sinalizar a ambiguidade no MR em vez de decidir sozinho.

## Onde declarar o início do changelog

Tags anteriores à adoção deste processo não são reconstruídas
retroativamente. O `CHANGELOG.md` passa a existir a partir da tag declarada
em sua própria seção inicial. Histórico anterior pode ser consultado pelos
MRs/PRs antigos no Git, se necessário.
