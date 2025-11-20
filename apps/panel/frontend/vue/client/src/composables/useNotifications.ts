/**
 * Composable para gerenciar notificações, som e indicadores visuais
 * Similar ao sistema do painel HTML original
 */

import { ref, onMounted, onUnmounted } from 'vue'
import type { NotificationAlert } from '@/types/dashboard'

interface UseNotificationsOptions {
  soundUrl?: string
  autoPlaySound?: boolean
}

export function useNotifications(options: UseNotificationsOptions = {}) {
  const { soundUrl = '', autoPlaySound = false } = options

  // Estado
  const notifications = ref<NotificationAlert[]>([])
  const isSoundEnabled = ref(false)
  const audioElement = ref<HTMLAudioElement | null>(null)
  const seenTicketIds = ref<Set<string | number>>(new Set())
  const lastNotificationTime = ref<number>(0)

  /**
   * Inicializa o elemento de áudio
   */
  const initializeAudio = () => {
    if (!audioElement.value) {
      audioElement.value = new Audio()
      audioElement.value.preload = 'auto'
    }
    if (soundUrl) {
      audioElement.value.src = soundUrl
    }
  }

  /**
   * Ativa o áudio (necessário para navegadores modernos)
   */
  const enableAudio = () => {
    if (isSoundEnabled.value) return

    isSoundEnabled.value = true
    console.log('[Notifications] Áudio ativado pelo usuário')

    // Toca um som de confirmação
    if (autoPlaySound) {
      playNotificationSound(true)
    }
  }

  /**
   * Toca som de notificação
   */
  const playNotificationSound = async (forcePlay = false) => {
    if (!isSoundEnabled.value && !forcePlay) {
      console.log('[Notifications] Som desativado')
      return
    }

    if (!audioElement.value || !audioElement.value.src) {
      console.log('[Notifications] Arquivo de som não configurado')
      return
    }

    try {
      audioElement.value.currentTime = 0
      await audioElement.value.play()
      console.log('[Notifications] Som tocado')
    } catch (error) {
      console.error('[Notifications] Erro ao tocar som:', error)
      isSoundEnabled.value = false
    }
  }

  /**
   * Adiciona notificação
   */
  const addNotification = (notification: NotificationAlert) => {
    notifications.value.push(notification)
    lastNotificationTime.value = Date.now()

    // Remove notificação após 5 segundos
    setTimeout(() => {
      notifications.value = notifications.value.filter(n => n !== notification)
    }, 5000)

    console.log('[Notifications] Notificação adicionada:', notification.type)
  }

  /**
   * Processa alerta de novo ticket
   */
  const handleNewTicketAlert = async (alert: NotificationAlert) => {
    const ticketId = alert.data.id

    // Verifica se é novo
    if (!seenTicketIds.value.has(ticketId)) {
      seenTicketIds.value.add(ticketId)

      // Toca som se habilitado
      if (isSoundEnabled.value && alert.data.soundUrl) {
        // Atualiza URL do som se fornecida
        if (audioElement.value) {
          audioElement.value.src = alert.data.soundUrl
        }
        await playNotificationSound()
      }

      // Adiciona notificação visual
      addNotification(alert)
    }
  }

  /**
   * Processa alerta de atualização de projeto
   */
  const handleProjectUpdateAlert = async (alert: NotificationAlert) => {
    // Toca som se crítico
    if (alert.data.severity === 'critical' && isSoundEnabled.value && alert.data.soundUrl) {
      if (audioElement.value) {
        audioElement.value.src = alert.data.soundUrl
      }
      await playNotificationSound()
    }

    addNotification(alert)
  }

  /**
   * Processa alerta crítico
   */
  const handleCriticalAlert = async (alert: NotificationAlert) => {
    // Sempre toca som para alertas críticos
    if (alert.data.soundUrl) {
      if (audioElement.value) {
        audioElement.value.src = alert.data.soundUrl
      }
      await playNotificationSound(true)
    }

    addNotification(alert)
  }

  /**
   * Processa notificação baseada no tipo
   */
  const processNotification = async (notification: NotificationAlert) => {
    switch (notification.type) {
      case 'new_ticket_alert':
        await handleNewTicketAlert(notification)
        break
      case 'project_update_alert':
        await handleProjectUpdateAlert(notification)
        break
      case 'critical_alert':
        await handleCriticalAlert(notification)
        break
      default:
        addNotification(notification)
    }
  }

  /**
   * Atualiza URL do som
   */
  const setSoundUrl = (url: string) => {
    if (audioElement.value) {
      audioElement.value.src = url
    }
  }

  /**
   * Limpa notificações
   */
  const clearNotifications = () => {
    notifications.value = []
  }

  /**
   * Reseta IDs de tickets vistos (para teste)
   */
  const resetSeenTickets = () => {
    seenTicketIds.value.clear()
  }

  // Ciclo de vida
  onMounted(() => {
    initializeAudio()

    // Listeners para ativar áudio
    document.addEventListener('click', enableAudio, { once: true })
    document.addEventListener('touchstart', enableAudio, { once: true })
  })

  onUnmounted(() => {
    document.removeEventListener('click', enableAudio)
    document.removeEventListener('touchstart', enableAudio)
  })

  return {
    // Estado
    notifications,
    isSoundEnabled,
    lastNotificationTime,

    // Métodos
    enableAudio,
    playNotificationSound,
    addNotification,
    processNotification,
    setSoundUrl,
    clearNotifications,
    resetSeenTickets,
    handleNewTicketAlert,
    handleProjectUpdateAlert,
    handleCriticalAlert
  }
}
