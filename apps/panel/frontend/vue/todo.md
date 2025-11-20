# Vue.js 3 NOC Dashboard - TODO

## Fase 1: Configuração do Projeto Vue.js 3
- [x] Remover arquivos React (App.tsx, Home.tsx)
- [x] Instalar dependências Vue 3 (vue, vue-router, pinia)
- [x] Configurar Tailwind CSS para tema Dark/Slate
- [x] Criar estrutura de diretórios para componentes Vue

## Fase 2: Layout Principal
- [x] Criar AppLayout.vue com Header Fixo, Sidebar Fixo e Conteúdo Dinâmico
- [x] Implementar estética Dark/Slate (cores, tipografia monospace)
- [x] Criar componentes de navegação (Sidebar)

## Fase 3: Header de Monitoramento
- [x] Implementar Relógio Digital em tempo real (HH:MM:SS)
- [x] Criar Indicador de Conexão WebSocket (ponto verde/vermelho)
- [x] Gerar e exibir ID Único do Cliente (Kiosk-XYZ)
- [x] Implementar lógica de conexão WebSocket persistente

## Fase 4: Componentes de Tela
- [x] Criar TicketsView.vue (5 colunas: Status, Abertura, Entidade, Título, Urgência)
- [x] Criar ProjectsView.vue (Título + 3 Contadores)
- [x] Criar RemoteControlView.vue (Interface administrativa)
- [x] Implementar dados simulados/mock API

## Fase 5: Lógica de Roteamento Dinâmico
- [x] Implementar roteamento dinâmico via activeScreen (componentes dinâmicos)
- [x] Implementar comando `remote_switch` no RemoteControlView.vue
- [x] Testar troca de views via WebSocket

## Fase 6: Revisão e Testes
- [x] Testar layout responsivo
- [x] Testar funcionalidade WebSocket
- [x] Testar troca de views
- [x] Validar estética Dark/NOC Mode

## Fase 7: Entrega
- [x] Preparar código-fonte para entrega
- [x] Criar documentação de uso
- [x] Salvar checkpoint final

## Adaptação para Setor de TI (Tickets e Projetos)
- [x] Atualizar TicketsView.vue com dados relevantes (atribuição, prioridade, tempo de resposta)
- [x] Redesenhar ProjectsView.vue para projetos de TI (status, equipes, métricas)
- [x] Melhorar RemoteControlView.vue com funcionalidades administrativas
- [x] Adicionar Dashboard com KPIs de desempenho
- [x] Atualizar terminologia e labels para operações de TI
- [x] Revisar e testar adaptações
- [x] Salvar novo checkpoint

## Aplicação de Cores Customizadas
- [x] Adicionar variáveis de cor customizadas ao index.css
- [x] Refatorar TicketsView.vue com cores de urgência
- [x] Refatorar DashboardView.vue com cores de status
- [x] Refatorar ProjectsView.vue com cores de status
- [x] Revisar e testar cores em todas as views
- [x] Salvar checkpoint final com cores customizadas

## Refatoração para WebSocket + Django Channels
- [x] Criar composable useWebSocket para gerenciar conexão persistente
- [x] Criar composable useNotifications para gerenciar notificações e som
- [x] Refatorar AppSidebar.vue com ícones compactos e tooltips
- [x] Criar tipos TypeScript para estrutura de dados (dashboard.ts)
- [x] Criar componente TestPanel para simular mensagens WebSocket
- [x] Atualizar App.vue para integrar WebSocket e notificações
- [x] Criar documentação de integração com Django Channels
- [ ] Salvar checkpoint final com WebSocket integrado
