# MoreFunctionsForGLPI

Backend Django que estende uma instância [GLPI](https://glpi-project.org/) (gestão de ativos de TI e chamados) com funcionalidades que o GLPI não oferece nativamente: um dashboard de acompanhamento de chamados em tempo real, um subsistema de impressão de etiquetas de patrimônio, geração de laudos técnicos de baixa/reparo, SSO a partir do GLPI e automação via webhook que aplica mudanças de status de volta no GLPI.

Roda embutido em um `<iframe>` dentro do próprio GLPI, e também pode ser empacotado como um executável standalone para Windows.

## Funcionalidades

- **Dashboard NOC** — painel de chamados/KPIs em tempo real (Vue 3 + WebSocket via Django Channels), com controle remoto de tela para exibições tipo kiosk.
- **Impressão de etiquetas** — editor visual de layout de etiqueta e impressão via um microsserviço externo.
- **Laudos de Baixa Patrimonial** e **Protocolos de Reparo** — geração de PDF a partir de dados copiados do GLPI, com fluxo de aprovação/travamento e opção de aplicar a baixa de volta no GLPI.
- **SSO com GLPI** — login no Django autenticado por um payload assinado emitido pelo GLPI.
- **Automação via webhook** — regras configuráveis que mudam o status de ativos no GLPI conforme a categoria/status de um chamado.

Um catálogo funcional completo (por app) está em `docs/features.md`.

## Arquitetura

Visão detalhada da arquitetura, dos apps (`dbcom`, `glpiintegrator`, `panel`, `printer`, `reports`) e dos padrões usados no projeto está em [`CLAUDE.md`](./CLAUDE.md).

## Rodando em desenvolvimento

Requisitos: Python 3.12+, MySQL/MariaDB, Redis (o `CHANNEL_LAYERS` é Redis-backed, não há fallback em memória configurado).

```bash
python -m venv venv
venv\Scripts\activate          # Windows
cp .envexample .env            # preencher as variáveis (ver .envexample)
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`migrations/` está no `.gitignore` — não são versionadas neste repositório, então `makemigrations` roda contra o estado do seu próprio banco.

### Frontend do dashboard (Vue)

O dashboard NOC tem um frontend separado em `apps/panel/frontend/vue/` (Vue 3 + Vite + Tailwind 4 + TypeScript, pnpm):

```bash
cd apps/panel/frontend/vue
pnpm install
pnpm dev        # servidor de dev na porta 3000
```

## Build do executável standalone

O app de impressão de etiquetas pode ser empacotado como um `.exe` Windows autocontido (Django + `waitress`), sem precisar de um deploy de servidor completo:

```bash
pyinstaller DirectLabelPrinter.spec
```

O entrypoint desse empacotamento é `run.py` (não `manage.py`). Rodar `run.py postinstall` (ou o `.exe` equivalente) gera o `.env`, aplica as migrações e cria um superusuário padrão na primeira instalação.

## Versionamento

Este projeto segue [Semantic Versioning](https://semver.org/lang/pt-BR/) e mantém um [`CHANGELOG.md`](./CHANGELOG.md) no formato [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/). Critérios de bump e o processo de changelog/PR estão em [`docs/versioning.md`](./docs/versioning.md).

## Documentação adicional

- [`CLAUDE.md`](./CLAUDE.md) — arquitetura, padrões de código, comandos.
- [`docs/versioning.md`](./docs/versioning.md) — critérios de versionamento e fluxo de changelog.
- [`TODO.md`](./TODO.md) — trabalho de manutenção em andamento.
