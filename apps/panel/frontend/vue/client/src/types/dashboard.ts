/**
 * Tipos e interfaces para o painel de TI
 * Definem a estrutura de dados enviada pelo Django Channels
 */

// ============ TICKETS ============
export interface Ticket {
  id: string | number
  title: string
  description: string
  assignedTo: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'open' | 'in_progress' | 'closed'
  createdAt: string // ISO 8601
  updatedAt: string // ISO 8601
  entity?: string
  urgency?: string
}

export interface TicketsData {
  type: 'tickets_update'
  data: Ticket[]
  counters: {
    critical: number
    high: number
    medium: number
    low: number
    total: number
  }
  timestamp: string
}

// ============ PROJETOS ============
export interface Project {
  id: string | number
  name: string
  responsible: string
  status: 'planning' | 'in_progress' | 'testing' | 'completed'
  completed: number
  inProgress: number
  pending: number
  progress: number
  dueDate: string
  updatedAt: string
}

export interface ProjectsData {
  type: 'projects_update'
  data: Project[]
  timestamp: string
}

// ============ DASHBOARD ============
export interface TeamMember {
  id: string | number
  name: string
  role: string // 'technician' | 'analyst'
  specialization: string
  available: boolean
  assignedCount: number
}

export interface DashboardKPIs {
  openTickets: number
  avgResponseTime: string
  resolutionRate: number
  customerSatisfaction: number
  surveyCount: number
}

export interface DashboardActivity {
  id: string | number
  timestamp: string
  description: string
  type: 'assignment' | 'progress' | 'closed' | 'new' | 'escalation'
  severity?: 'low' | 'medium' | 'high' | 'critical'
}

export interface DashboardData {
  type: 'dashboard_update'
  kpis: DashboardKPIs
  technicians: TeamMember[]
  analysts: TeamMember[]
  recentActivity: DashboardActivity[]
  timestamp: string
}

// ============ NOTIFICAÇÕES ============
export interface NotificationAlert {
  type: 'new_ticket_alert' | 'project_update_alert' | 'critical_alert'
  data: {
    id: string | number
    title: string
    severity: 'low' | 'medium' | 'high' | 'critical'
    soundUrl?: string // URL do Django para tocar som
  }
  timestamp: string
}

// ============ CONTROLE REMOTO ============
export interface RemoteCommand {
  type: 'remote_switch' | 'refresh_data' | 'settings_update'
  target?: string // 'dashboard' | 'tickets' | 'projects' | 'remote'
  payload?: any
}

// ============ IDENTIFICAÇÃO DO CLIENTE ============
export interface ClientIdentification {
  type: 'identify'
  clientId: string
  availableScreens?: string[]
  timestamp: string
}

// ============ MENSAGENS WEBSOCKET ============
export type WebSocketMessage =
  | TicketsData
  | ProjectsData
  | DashboardData
  | NotificationAlert
  | RemoteCommand
  | ClientIdentification
  | { type: 'connection_established'; clientId: string; client_ip?: string }
  | { type: 'client_ip_response'; client_ip: string }
  | { type: 'change_screen'; screen: string }
  | { type: 'error'; message: string }

// ============ ESTADO DA APLICAÇÃO ============
export interface AppState {
  clientId: string
  wsConnected: boolean
  lastUpdate: string
  tickets: Ticket[]
  projects: Project[]
  dashboard: DashboardData | null
  notifications: NotificationAlert[]
  activeScreen: 'dashboard' | 'tickets' | 'projects' | 'remote'
}
