<template>
  <div v-if="visible"
    class="fixed bottom-4 right-4 w-96 bg-slate-800 border-2 border-purple-500 rounded-lg p-6 shadow-2xl z-40 max-h-96 overflow-y-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-4 pb-4 border-b border-slate-700">
      <h3 class="text-lg font-bold text-purple-400 font-mono">Painel de Teste</h3>
      <button @click="$emit('close')" class="text-slate-400 hover:text-slate-200 transition-colors">
        <span class="material-icons">close</span>
      </button>
    </div>

    <!-- Simulador de Estados de Conexão -->
    <div class="space-y-4">

      <!-- Simulador de Novo Ticket -->
      <div class="pt-4 border-t border-slate-700">
        <h4 class="text-sm font-bold text-slate-300 mb-2 font-mono">Simular Novo Ticket</h4>
        <div class="space-y-2">
          <input v-model="newTicketTitle" type="text" placeholder="Título do ticket"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500" />
          <select v-model="newTicketPriority"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-slate-100 focus:outline-none focus:border-purple-500">
            <option value="critical">Crítico</option>
            <option value="high">Alto</option>
            <option value="medium">Médio</option>
            <option value="low">Baixo</option>
          </select>
          <button @click="sendNewTicket" :disabled="!newTicketTitle"
            class="w-full px-3 py-2 bg-red-600 hover:bg-red-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-sm font-bold text-white transition-colors">
            Enviar Novo Ticket
          </button>
        </div>
      </div>

      <!-- Simulador de Atualização de Projeto -->
      <div class="pt-4 border-t border-slate-700">
        <h4 class="text-sm font-bold text-slate-300 mb-2 font-mono">Simular Atualização Projeto</h4>
        <div class="space-y-2">
          <input v-model="projectUpdateTitle" type="text" placeholder="Nome do projeto"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500" />
          <input v-model.number="projectProgress" type="number" min="0" max="100" placeholder="Progresso (%)"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500" />
          <button @click="sendProjectUpdate" :disabled="!projectUpdateTitle"
            class="w-full px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-sm font-bold text-white transition-colors">
            Enviar Atualização
          </button>
        </div>
      </div>

      <!-- Simulador de Som -->
      <div class="pt-4 border-t border-slate-700">
        <h4 class="text-sm font-bold text-slate-300 mb-2 font-mono">Testar Som</h4>
        <div class="space-y-2">
          <input v-model="soundUrl" type="text" placeholder="URL do som"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500" />
          <button @click="playTestSound" :disabled="!soundUrl"
            class="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-700 disabled:bg-slate-600 disabled:cursor-not-allowed rounded text-sm font-bold text-white transition-colors">
            Tocar Som
          </button>
        </div>
      </div>

      <!-- Simulador de Comando Remoto -->
      <div class="pt-4 border-t border-slate-700">
        <h4 class="text-sm font-bold text-slate-300 mb-2 font-mono">Comando Remoto</h4>
        <div class="space-y-2">
          <select v-model="remoteTarget"
            class="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-sm text-slate-100 focus:outline-none focus:border-purple-500">
            <option value="dashboard">Dashboard</option>
            <option value="tickets">Tickets</option>
            <option value="projects">Projetos</option>
            <option value="remote">Administração</option>
          </select>
          <button @click="sendRemoteCommand"
            class="w-full px-3 py-2 bg-green-600 hover:bg-green-700 rounded text-sm font-bold text-white transition-colors">
            Enviar Comando
          </button>
        </div>
      </div>

      <!-- Status -->
      <div class="pt-4 border-t border-slate-700">
        <h4 class="text-sm font-bold text-slate-300 mb-2 font-mono">Status</h4>
        <div class="text-xs text-slate-400 space-y-1 font-mono">
          <div>Cliente ID: <span class="text-slate-200">{{ clientId }}</span></div>
          <div>IP: <span class="text-slate-200">{{ clientIp }}</span></div>
          <div>
            Conexão:
            <span :class="[
              connectionStatus === 'connected' ? 'text-green-400' :
                connectionStatus === 'connecting' ? 'text-yellow-400' :
                  'text-red-400'
            ]">
              {{ connectionStatusLabel }}
            </span>
          </div>
          <div>Som Ativado: <span :class="soundEnabled ? 'text-yellow-400' : 'text-slate-500'">{{ soundEnabled ? 'Sim' :
              'Não' }}</span></div>
          <div>Intervalo de Atualização: <span class="text-slate-200">{{ settings.fetch_interval_seconds }}s</span>
          </div>
          <button @click="forceRefreshData"
            class="w-full px-3 py-2 mt-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-bold text-white transition-colors">
            Forçar Atualização de Dados
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'

const emit = defineEmits<{
  'close': []
  'send-new-ticket': [data: any]
  'send-project-update': [data: any]
  'send-remote-command': [target: string]
  'play-sound': [url: string]
}>()

const props = defineProps<{
  visible: boolean
  clientId: string
  clientIp: string
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'reconnecting' | 'error'
  soundEnabled: boolean
}>()

// Access settings from useWebSocket
const { settings, requestDataRefresh } = useWebSocket()

// Estados locais
const newTicketTitle = ref('')
const newTicketPriority = ref('high')
const projectUpdateTitle = ref('')
const projectProgress = ref(50)
const soundUrl = ref(settings.value.notification_sound_url || 'https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3')
const remoteTarget = ref('dashboard')

// Watch for changes in settings.notification_sound_url
watch(() => settings.value.notification_sound_url, (newUrl) => {
  if (newUrl) {
    soundUrl.value = newUrl
  }
}, { immediate: true })

// Computed
const connectionStatusLabel = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'Online'
    case 'connecting':
      return 'Conectando...'
    case 'disconnected':
      return 'Offline'
    case 'reconnecting':
      return 'Reconectando...'
    case 'error':
      return 'Erro'
    default:
      return 'Desconhecido'
  }
})

const sendNewTicket = () => {
  if (!newTicketTitle.value) {
    alert('Preencha o título do ticket')
    return
  }

  emit('send-new-ticket', {
    type: 'new_ticket_alert',
    data: {
      id: `TEST-${Date.now()}`,
      title: newTicketTitle.value,
      severity: newTicketPriority.value,
      soundUrl: soundUrl.value
    },
    timestamp: new Date().toISOString()
  })

  newTicketTitle.value = ''
}

const sendProjectUpdate = () => {
  if (!projectUpdateTitle.value) {
    alert('Preencha o nome do projeto')
    return
  }

  emit('send-project-update', {
    type: 'project_update_alert',
    data: {
      id: `PROJ-${Date.now()}`,
      title: projectUpdateTitle.value,
      severity: 'medium',
      soundUrl: soundUrl.value
    },
    timestamp: new Date().toISOString()
  })

  projectUpdateTitle.value = ''
  projectProgress.value = 50
}

const playTestSound = () => {
  if (!soundUrl.value) {
    alert('Preencha a URL do som')
    return
  }

  emit('play-sound', soundUrl.value)
}

const sendRemoteCommand = () => {
  emit('send-remote-command', remoteTarget.value)
}

const forceRefreshData = () => {
  requestDataRefresh('dashboard')
  requestDataRefresh('tickets')
}
</script>

<style scoped>
/* Estilos do painel de teste */
</style>
