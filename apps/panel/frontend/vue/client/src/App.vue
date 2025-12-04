<template>
  <div class="flex h-screen bg-slate-900">
    <!-- Sidebar -->
    <AppSidebar :activeMenu="activeScreen" :wsConnected="wsConnected" :soundEnabled="isSoundEnabled"
      @select-menu="activeScreen = $event" @toggle-sound="toggleSound"
      @toggle-test-panel="showTestPanel = !showTestPanel" />

    <!-- Main Content -->
    <div class="flex-1 flex flex-col ml-20">
      <!-- Header -->
      <AppHeader :clientId="wsClientId" :clientIp="clientIp"
        :connectionStatus="connectionStatus" :currentTime="currentTime"
        :timezone="timezone" />

      <!-- Views Container -->
      <div class="flex-1 overflow-y-auto pt-16">
        <transition name="fade" mode="out-in">
          <component :is="activeScreenComponent" />
        </transition>
      </div>
    </div>

    <!-- Notifications Toast -->
    <div class="fixed top-24 right-4 space-y-2 z-30">
      <transition-group name="notification">
        <div v-for="notification in notificationAlerts" :key="notification.data.id"
          class="bg-slate-800 border-l-4 border-red-500 p-4 rounded shadow-lg max-w-sm">
          <div class="flex items-start gap-3">
            <span class="material-icons text-red-500 flex-shrink-0">warning</span>
            <div>
              <h4 class="font-bold text-slate-100">{{ notification.data.title }}</h4>
              <p class="text-sm text-slate-400">Prioridade: {{ notification.data.severity }}</p>
            </div>
          </div>
        </div>
      </transition-group>
    </div>

    <!-- Test Panel -->
    <TestPanel v-if="showTestPanel" :visible="showTestPanel" :clientId="wsClientId" :clientIp="clientIp"
      :connectionStatus="connectionStatus" :soundEnabled="isSoundEnabled" @close="showTestPanel = false"
      @send-new-ticket="handleTestNewTicket" @send-project-update="handleTestProjectUpdate"
      @send-remote-command="handleTestRemoteCommand" @play-sound="handleTestPlaySound" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
import TestPanel from './components/TestPanel.vue'
import TicketsView from './views/TicketsView.vue'
import ProjectsView from './views/ProjectsView.vue'
import DashboardView from './views/DashboardView.vue'
import RemoteControlView from './views/RemoteControlView.vue'
import { useWebSocket } from './composables/useWebSocket'
import { useNotifications } from './composables/useNotifications'
import type { NotificationAlert, WebSocketMessage, Ticket } from './types/dashboard'

// WebSocket
const {
  isConnected: wsConnected,
  connectionStatus,
  clientId: wsClientId,
  settings,
  lastMessage,
  send: sendWebSocketMessage
} = useWebSocket({
  availableScreens: ['dashboard', 'tickets', 'projects', 'remote']
})

// Notificações
const {
  isSoundEnabled,
  processNotification,
  playNotificationSound,
  setSoundUrl,
  toggleSound: toggleNotificationSound,
  notifications: notificationAlerts // Renamed to avoid conflict with local notifications ref
} = useNotifications()

const seenTicketIds = ref<Set<string | number>>(new Set());
let isInitialTicketsLoad = true;


// Watch for settings changes and update the sound URL
watch(() => settings.value.notification_sound_url, (newUrl) => {
  if (newUrl) {
    setSoundUrl(newUrl)
    console.log(`[App] Notification sound URL set to: ${newUrl}`)
  }
}, { immediate: true })

// Watch for screen change requests and new tickets
watch(lastMessage, (msg: WebSocketMessage | null) => {
  if (!msg) return;

  // Handle screen change
  if (msg.type === 'change_screen' && msg.screen) {
    console.log(`[App] Changing screen to: ${msg.screen}`);
    if (['dashboard', 'tickets', 'projects', 'remote'].includes(msg.screen)) {
      activeScreen.value = msg.screen as any;
    }
  }

  // Handle new ticket detection
  if (msg.type === 'tickets_update' && msg.data) {
    // Ensure msg.data is treated as an array of Ticket objects
    const incomingTickets = msg.data as Ticket[]; 
    const incomingTicketIds = incomingTickets.map((t: Ticket) => String(t.id));

    if (isInitialTicketsLoad) {
      seenTicketIds.value = new Set(incomingTicketIds);
      isInitialTicketsLoad = false;
    } else {
      let newTicketFound = false;
      for (const ticketData of incomingTickets) { 
        const ticketId = String(ticketData.id);
        if (!seenTicketIds.value.has(ticketId)) {
          // It's a new ticket, trigger alert and play sound
          console.log('[App] New ticket detected. Playing sound and showing notification.');
          playNotificationSound();

          // Construct and process the notification alert
          const newTicketAlert: NotificationAlert = {
            type: 'new_ticket_alert',
            data: {
              id: ticketId,
              title: ticketData.Titulo || `Ticket #${ticketId}`, // Use "Titulo" from backend data
              severity: ticketData.Urgencia || 'medium', // Use "Urgencia" from backend data
            },
            timestamp: new Date().toISOString()
          };
          processNotification(newTicketAlert); // This adds to notificationAlerts ref

          newTicketFound = true; // Only play sound once and show notification for the first new one
          break; 
        }
      }
      
      // Always update seen tickets after processing the update to avoid repeated notifications
      seenTicketIds.value = new Set(incomingTicketIds);
    }
  }
});


// Estado da aplicação
const activeScreen = ref<'dashboard' | 'tickets' | 'projects' | 'remote'>('tickets')
const showTestPanel = ref(false)
const currentTime = ref<string>('00:00:00')
const timezone = ref<string>('America/Porto_Velho')
const clientIp = ref<string>('Detectando...')
let timeInterval: ReturnType<typeof setInterval> | null = null

// Componentes de tela
const viewComponents = {
  dashboard: DashboardView,
  tickets: TicketsView,
  projects: ProjectsView,
  remote: RemoteControlView
}

const activeScreenComponent = computed(() => viewComponents[activeScreen.value])

// Atualizar relógio com fuso horário local
const updateClock = () => {
  const now = new Date()

  // Formatar para o fuso horário America/Porto_Velho
  const formatter = new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Porto_Velho',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })

  const parts = formatter.formatToParts(now)
  const hour = parts.find(p => p.type === 'hour')?.value || '00'
  const minute = parts.find(p => p.type === 'minute')?.value || '00'
  const second = parts.find(p => p.type === 'second')?.value || '00'

  currentTime.value = `${hour}:${minute}:${second}`
}

// Handlers para o painel de teste
const handleTestNewTicket = async (data: NotificationAlert) => {
  await processNotification(data)
}

const handleTestProjectUpdate = async (data: NotificationAlert) => {
  await processNotification(data)
}

const handleTestRemoteCommand = (target: string) => {
  activeScreen.value = target as any
  console.log(`[Test] Comando remoto: alternar para ${target}`)
}

const handleTestPlaySound = async (url: string) => {
  setSoundUrl(url)
  await playNotificationSound(true)
}

// Toggle de som
const toggleSound = () => {
  toggleNotificationSound()
}

// Detectar IP local do cliente via WebRTC
const detectClientIp = async () => {
  try {
    console.log('[IP Detection] Iniciando detecção via WebRTC...')
    const pc = new RTCPeerConnection({ iceServers: [] })

    pc.createDataChannel('')
    pc.createOffer().then(offer => pc.setLocalDescription(offer))

    pc.onicecandidate = (ice) => {
      if (!ice || !ice.candidate) return

      const ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3})/
      const ipAddress = ipRegex.exec(ice.candidate.candidate)?.[1]

      if (ipAddress) {
        console.log('[IP Detection] Candidato encontrado:', ipAddress)
        // Ignora localhost e máscaras comuns de docker/vpn se desejar, 
        // mas para "saber o IP local" geralmente queremos o 192.168.x.x
        if (!ipAddress.startsWith('127.') && !ipAddress.startsWith('255.')) {
          clientIp.value = ipAddress
          pc.close()
        }
      }
    }
  } catch (e) {
    console.error('[IP Detection] Erro ao detectar IP local:', e)
  }
}

// Lifecycle
onMounted(() => {
  updateClock()
  timeInterval = setInterval(updateClock, 1000)

  // Tenta detectar IP localmente primeiro
  detectClientIp()

  // Iniciar conexão WebSocket (Gerenciado apenas aqui no App.vue)
  const { connect } = useWebSocket()
  connect()
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }

  // Fechar conexão ao sair da aplicação
  const { disconnect } = useWebSocket()
  disconnect()
})</script>

<style>
/* Animações de notificação */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(30px);
}

/* Page transition animation */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
