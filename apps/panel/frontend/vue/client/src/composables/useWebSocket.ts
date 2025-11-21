/**
 * Composable para gerenciar conexão WebSocket com Django Channels
 * Suporta reconexão automática e gerenciamento de mensagens
 * Implementa Singleton Pattern para compartilhar conexão
 */

import { ref, computed } from 'vue'
import type { WebSocketMessage, ClientIdentification } from '@/types/dashboard'

interface UseWebSocketOptions {
  url?: string
  autoReconnect?: boolean
  reconnectDelay?: number
  maxReconnectAttempts?: number
  availableScreens?: string[]
}

// Estado compartilhado (Singleton)
const ws = ref<WebSocket | null>(null)
const isConnected = ref(false)
const lastMessage = ref<WebSocketMessage | null>(null)
const error = ref<string | null>(null)
const reconnectAttempts = ref(0)
const clientIp = ref('Detectando...')
const settings = ref({
  fetch_interval_seconds: 30,
  notification_sound_url: ''
})
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null

// Gera ID único do cliente (persistente)
const generateClientId = (): string => {
  const storageKey = 'glpi_panel_display_id'
  let id = localStorage.getItem(storageKey)

  if (!id) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    id = 'DISPLAY-'
    for (let i = 0; i < 5; i++) {
      id += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    localStorage.setItem(storageKey, id)
  }
  return id
}

const clientId = ref(generateClientId())

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const wsBaseUrl = import.meta.env.VITE_WS_BASE_URL;

  let defaultUrl;
  if (wsBaseUrl) {
    // Usa a URL do .env se ela existir.
    defaultUrl = `${wsBaseUrl}/ws/panel/`;
  } else {
    // Fallback para o comportamento antigo: constrói a URL a partir do host da página.
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    defaultUrl = `${protocol}//${window.location.host}/ws/panel/`;
    console.warn('[WebSocket] VITE_WS_BASE_URL não está definida. Usando URL relativa:', defaultUrl);
  }

  const {
    url = defaultUrl,
    autoReconnect = true,
    reconnectDelay = 5000,
    maxReconnectAttempts = 10,
    availableScreens = []
  } = options

  /**
   * Conecta ao servidor WebSocket
   */
  const connect = () => {
    if (ws.value && (ws.value.readyState === WebSocket.OPEN || ws.value.readyState === WebSocket.CONNECTING)) {
      console.log('[WebSocket] Já conectado ou conectando...')
      return
    }

    try {
      console.log(`[WebSocket] Conectando a ${url}...`)
      ws.value = new WebSocket(url)

      ws.value.onopen = () => {
        isConnected.value = true
        error.value = null
        reconnectAttempts.value = 0
        console.log('[WebSocket] Conectado com sucesso')

        // Envia identificação do cliente
        const identification: ClientIdentification = {
          type: 'identify',
          clientId: clientId.value,
          availableScreens: availableScreens,
          timestamp: new Date().toISOString()
        }
        send(identification)

        // Solicita IP
        requestIp()
      }

      ws.value.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as WebSocketMessage
          lastMessage.value = message
          // console.log('[WebSocket] Mensagem recebida:', message.type)

          // Quando o servidor envia o IP, armazenar
          if (message.type === 'connection_established' && (message as any).client_ip) {
            clientIp.value = (message as any).client_ip
            console.log('[WebSocket] IP recebido:', clientIp.value)
          }

          if (message.type === 'client_ip_response' && (message as any).client_ip) {
            clientIp.value = (message as any).client_ip
            console.log('[WebSocket] IP atualizado:', clientIp.value)
          }

          if (message.type === 'settings_update' && (message as any).settings) {
            settings.value = (message as any).settings
            console.log('[WebSocket] Settings updated:', settings.value)
          }
        } catch (e) {
          console.error('[WebSocket] Erro ao parsear mensagem:', e)
        }
      }

      ws.value.onerror = (event) => {
        error.value = 'Erro de conexão WebSocket'
        console.error('[WebSocket] Erro detalhado:', event)
      }

      ws.value.onclose = (event) => {
        isConnected.value = false
        console.log(`[WebSocket] Desconectado. Código: ${event.code}, Razão: ${event.reason}, Limpo: ${event.wasClean}`)

        // Tenta reconectar
        if (autoReconnect && reconnectAttempts.value < maxReconnectAttempts) {
          reconnectAttempts.value++
          const delay = reconnectDelay * Math.pow(1.5, reconnectAttempts.value - 1)
          console.log(
            `[WebSocket] Reconectando em ${Math.round(delay / 1000)}s (tentativa ${reconnectAttempts.value}/${maxReconnectAttempts})...`
          )
          reconnectTimeout = setTimeout(() => {
            ws.value = null // Reset para permitir nova conexão
            connect()
          }, delay)
        } else if (reconnectAttempts.value >= maxReconnectAttempts) {
          error.value = 'Falha ao conectar após múltiplas tentativas'
          console.error('[WebSocket] Máximo de tentativas de reconexão atingido')
        }
      }
    } catch (e) {
      error.value = `Erro ao conectar: ${String(e)}`
      console.error('[WebSocket] Erro de conexão:', e)
    }
  }

  /**
   * Aguarda a conexão ser estabelecida
   */
  const waitForConnection = (): Promise<void> => {
    return new Promise((resolve) => {
      if (ws.value?.readyState === WebSocket.OPEN) {
        resolve()
        return
      }

      const checkInterval = setInterval(() => {
        if (ws.value?.readyState === WebSocket.OPEN) {
          clearInterval(checkInterval)
          resolve()
        }
      }, 100)

      // Timeout após 5s
      setTimeout(() => {
        clearInterval(checkInterval)
        resolve() // Resolve anyway to avoid hanging
      }, 5000)
    })
  }

  /**
   * Envia mensagem ao servidor
   */
  const send = async (message: any) => {
    if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
      // Se estiver conectando, aguarda
      if (ws.value?.readyState === WebSocket.CONNECTING) {
        await waitForConnection()
      } else {
        console.warn('[WebSocket] WebSocket não está conectado. Tentando conectar...')
        connect()
        await waitForConnection()
      }
    }

    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      try {
        ws.value.send(JSON.stringify(message))
        // console.log('[WebSocket] Mensagem enviada:', message.type)
      } catch (e) {
        console.error('[WebSocket] Erro ao enviar mensagem:', e)
      }
    } else {
      console.warn('[WebSocket] Falha ao enviar mensagem: Não conectado')
    }
  }

  /**
   * Desconecta do servidor
   */
  const disconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
    }
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
    isConnected.value = false
  }

  /**
   * Força reconexão
   */
  const forceReconnect = () => {
    disconnect()
    reconnectAttempts.value = 0
    setTimeout(connect, 1000)
  }

  /**
   * Envia comando remoto
   */
  const sendRemoteCommand = (target: string, payload?: any) => {
    send({
      type: 'remote_switch',
      target,
      payload,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Solicita atualização de dados
   */
  const requestDataRefresh = (view?: string) => {
    send({
      type: 'request_data',
      view,
      timestamp: new Date().toISOString()
    })
  }

  /**
   * Solicita o IP do cliente ao servidor
   */
  const requestIp = () => {
    send({
      type: 'request_ip',
      timestamp: new Date().toISOString()
    })
  }

  // Remover lifecycle hooks automáticos para evitar desconexão acidental
  // A conexão deve ser gerenciada pelo componente raiz (App.vue)

  // Computed properties
  const connectionStatus = computed(() => {
    if (isConnected.value) return 'connected'
    if (error.value) return 'error'
    if (reconnectAttempts.value > 0) return 'reconnecting'
    return 'disconnected'
  })

  return {
    // Estado
    isConnected,
    connectionStatus,
    lastMessage,
    error,
    clientId,
    clientIp,
    settings,
    reconnectAttempts,

    // Métodos
    connect,
    disconnect,
    forceReconnect,
    send,
    sendRemoteCommand,
    requestDataRefresh,
    requestIp
  }
}
