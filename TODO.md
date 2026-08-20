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

- [ ] **2. Análise completa do código: erros e redundâncias**
  Revisar `apps/dbcom`, `apps/glpiintegrator`, `apps/panel`, `apps/printer`,
  `apps/reports`, `core` procurando bugs, código morto, duplicação e
  inconsistências. Produzir um relatório com os achados.

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

- [ ] **5. Criar infraestrutura de changelog e Merge Request**
  Configurar `CHANGELOG.md` e o fluxo de MR conforme os comandos/skills
  do Claude Code (`changelog-mr`, `changelog-release`).

- [ ] **6. Criar template de Pull Request para o GitHub**
  `.github/PULL_REQUEST_TEMPLATE.md`, alinhado ao fluxo definido no item 5.

- [ ] **7. Analisar e implementar django-unfold no admin**
  Avaliar compatibilidade com Django 6.0.1 e com as customizações já
  existentes no admin deste projeto (templates de confirmação de action,
  singletons, inlines, CSP para iframe do GLPI) antes de instalar.

## Spec pausada (não faz parte deste TODO)

`docs/superpowers/specs/2026-08-20-baixa-patrimonial-item-tracking-design.md`
e seu plano em `docs/superpowers/plans/2026-08-20-baixa-patrimonial-item-tracking.md`
ficam parados até o usuário retomar — não iniciar implementação sem pedido
explícito.
