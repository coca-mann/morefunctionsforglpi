# Vue.js 3 - Painel de Gerenciamento de Tickets e Projetos

Uma aplicação profissional para **Gerenciamento de Tickets e Projetos** em um setor de TI, desenvolvida com **Vue.js 3** (Composition API), **Tailwind CSS 4**, e **WebSocket** para controle remoto em tempo real. Ideal para técnicos de manutenção e analistas de sistemas acompanharem chamados, projetos e métricas de desempenho.

## Características Principais

### 1. **Layout Responsivo com Seções Fixas**
- **Header Fixo**: Barra superior com relógio digital, indicador de conexão WebSocket e ID único do cliente
- **Sidebar Fixo**: Menu de navegação à esquerda com opções de telas
- **Conteúdo Dinâmico**: Área principal que alterna entre diferentes visualizações

### 2. **Estética Dark/Slate**
- Paleta de cores **Dark/Slate** (fundo preto-azulado) para reduzir fadiga ocular
- Tipografia **monospace** para números e valores críticos
- Números em **negrito** e **grandes** para fácil leitura
- Indicadores visuais com cores semânticas (verde, amarelo, laranja, vermelho)

### 3. **Componentes de Tela**

#### **DashboardView.vue** - Dashboard de Desempenho
- **KPIs Principais**: Tickets Abertos, Tempo Médio de Resposta, Taxa de Resolução, Satisfação do Cliente
- **Equipe**: Lista de Técnicos de Manutenção e Analistas de Sistemas com status de disponibilidade
- **Atividade Recente**: Log de eventos e ações do sistema
- Dados simulados para demonstração

#### **TicketsView.vue** - Tickets de Manutenção
- Tabela com 6 colunas: **ID**, **Descrição**, **Atribuído a**, **Prioridade**, **Status**, **Tempo Decorrido**
- Contadores de topo mostrando tickets por prioridade (Crítico, Alto, Médio, Baixo)
- Badges coloridos para prioridade e status
- Dados simulados com exemplos reais de manutenção (servidor, impressora, notebook, etc)

#### **ProjectsView.vue** - Projetos de TI
- Grade com 3 projetos em andamento
- Informações: Responsável, Status (Planejamento, Em Andamento, Testes, Concluído)
- Métricas: Tarefas Concluídas, Em Progresso, Pendentes
- Barra de progresso visual e data de conclusão prevista
- Dados simulados para demonstração

#### **RemoteControlView.vue** - Administração
- Campo para visualizar e copiar o ID único do cliente
- Botões para enviar comandos de alternância de tela
- Status da conexão WebSocket
- Log de eventos em tempo real

### 4. **Lógica de WebSocket em Tempo Real**
- Conexão persistente com `/ws/dashboard_control/`
- Identificação automática do cliente com ID único (ex: `Kiosk-ABCDE`)
- Suporte ao comando `remote_switch` para alternar telas remotamente
- Reconexão automática com backoff exponencial
- Indicador visual do status da conexão (verde = conectado, vermelho = desconectado)

### 5. **Relógio Digital em Tempo Real**
- Exibição da hora atual em formato **HH:MM:SS**
- Atualização a cada segundo
- Fonte monospace para estabilidade visual

## Estrutura de Arquivos

```
client/src/
├── App.vue                    # Componente raiz com lógica de WebSocket
├── main.ts                    # Ponto de entrada da aplicação
├── index.css                  # Estilos globais e temas Tailwind
├── const.ts                   # Constantes da aplicação
├── components/
│   ├── AppHeader.vue          # Header fixo com relógio e indicador
│   └── AppSidebar.vue         # Sidebar com navegação
└── views/
    ├── DashboardView.vue      # Dashboard com KPIs e equipe
    ├── TicketsView.vue        # Visualização de tickets de manutenção
    ├── ProjectsView.vue       # Visualização de projetos de TI
    └── RemoteControlView.vue  # Interface de administração
```

## Instalação e Execução

### Pré-requisitos
- Node.js 18+
- pnpm (ou npm/yarn)

### Passos

1. **Instalar dependências**:
   ```bash
   pnpm install
   ```

2. **Iniciar o servidor de desenvolvimento**:
   ```bash
   pnpm dev
   ```

3. **Acessar a aplicação**:
   - Abra seu navegador em `http://localhost:3000`

4. **Build para produção**:
   ```bash
   pnpm build
   ```

## Uso da Aplicação

### Navegação
- Use o **Sidebar** à esquerda para alternar entre as telas
- Clique em "Dashboard", "Tickets", "Projetos" ou "Administração"

### Monitoramento
- Observe o **Header** para:
  - **Relógio Digital**: Hora atual em tempo real
  - **Indicador WebSocket**: Ponto verde (conectado) ou vermelho (desconectado)
  - **ID do Cliente**: Identificador único desta instância (ex: `Kiosk-ABCDE`)

### Dashboard
- Visualize KPIs de desempenho do setor de TI
- Acompanhe o status da equipe (técnicos e analistas)
- Veja atividades recentes do sistema

### Tickets
- Visualize todos os tickets de manutenção abertos
- Acompanhe prioridade, responsável e tempo decorrido
- Filtre por prioridade usando os contadores de topo

### Projetos
- Acompanhe o progresso de projetos de TI
- Veja responsáveis e status de cada projeto
- Monitore métricas de conclusão

### Administração
- Copie o ID único do cliente
- Envie comandos para alternar telas remotamente
- Acompanhe o log de eventos do sistema

## Integração com WebSocket Backend

A aplicação espera um servidor WebSocket em `/ws/dashboard_control/` que suporte:

### Mensagem de Identificação (Cliente → Servidor)
```json
{
  "type": "identify",
  "client_id": "Kiosk-ABCDE"
}
```

### Mensagem de Alternância de Tela (Servidor → Cliente)
```json
{
  "type": "remote_switch",
  "target": "dashboard"
}
```

**Valores válidos para `target`**: `dashboard`, `tickets`, `projects`, `remote`

## Personalização

### Alterar Cores
Edite o arquivo `client/src/index.css` para modificar a paleta de cores do tema Dark/Slate.

### Adicionar Novas Telas
1. Crie um novo arquivo em `client/src/views/` (ex: `NewView.vue`)
2. Importe em `App.vue`
3. Adicione ao objeto `viewComponents`
4. Adicione um item ao menu em `AppSidebar.vue`

### Conectar a API Real
Substitua os dados simulados em cada view por chamadas reais a uma API:
```typescript
const { data } = await fetch('/api/tickets/data').then(r => r.json())
```

## Tecnologias Utilizadas

- **Vue.js 3**: Framework reativo
- **Composition API**: API moderna do Vue 3
- **Tailwind CSS 4**: Framework de CSS utilitário
- **TypeScript**: Tipagem estática
- **WebSocket**: Comunicação em tempo real
- **nanoid**: Geração de IDs únicos

## Notas Importantes

- O ID do cliente é gerado aleatoriamente a cada carregamento da página
- A conexão WebSocket tenta reconectar automaticamente se desconectar
- Todos os dados exibidos são simulados para demonstração
- A aplicação é totalmente responsiva e otimizada para diferentes tamanhos de tela
- O painel é otimizado para operações de TI com técnicos de manutenção e analistas de sistemas

## Suporte e Contribuições

Para sugestões, bugs ou contribuições, entre em contato com a equipe de desenvolvimento.

---

**Versão**: 1.1.0  
**Última atualização**: Novembro 2025  
**Adaptado para**: Gerenciamento de Tickets e Projetos de TI
