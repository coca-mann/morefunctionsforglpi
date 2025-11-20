<template>
  <div class="p-6 space-y-6">
    <!-- Título -->
    <div>
      <h2 class="text-2xl font-bold text-slate-100 font-mono">Administração</h2>
      <p class="text-sm text-slate-400 mt-1">Ferramentas administrativas para gerenciar tickets e projetos</p>
    </div>
    
    <!-- Seção: ID do Cliente -->
    <div class="bg-slate-800 border border-slate-700 rounded p-6 space-y-4">
      <h3 class="text-lg font-bold text-slate-100 font-mono">ID Único do Cliente</h3>
      <div class="flex items-center gap-3">
        <input 
          type="text" 
          :value="clientId"
          readonly
          class="flex-1 bg-slate-900 border border-slate-700 rounded px-4 py-2 text-slate-100 font-mono text-sm"
        />
        <button 
          @click="copyToClipboard"
          class="px-4 py-2 bg-slate-700 hover:bg-slate-600 border border-slate-600 rounded text-slate-100 font-mono text-sm transition-colors"
        >
          {{ copied ? 'Copiado!' : 'Copiar' }}
        </button>
      </div>
    </div>
    
    <!-- Seção: Comandos de Controle -->
    <div class="bg-slate-800 border border-slate-700 rounded p-6 space-y-4">
      <h3 class="text-lg font-bold text-slate-100 font-mono">Comandos de Controle</h3>
      <p class="text-sm text-slate-400">Envie comandos para alternar a tela do dashboard</p>
      
      <div class="grid grid-cols-3 gap-4">
        <button 
          @click="sendCommand('tickets')"
          class="px-4 py-3 bg-blue-900 hover:bg-blue-800 border border-blue-700 rounded text-blue-300 font-mono text-sm transition-colors"
        >
          → Chamados
        </button>
        <button 
          @click="sendCommand('projects')"
          class="px-4 py-3 bg-purple-900 hover:bg-purple-800 border border-purple-700 rounded text-purple-300 font-mono text-sm transition-colors"
        >
          → Projetos
        </button>
        <button 
          @click="sendCommand('remote')"
          class="px-4 py-3 bg-green-900 hover:bg-green-800 border border-green-700 rounded text-green-300 font-mono text-sm transition-colors"
        >
          → Controle
        </button>
      </div>
    </div>
    
    <!-- Seção: Status da Conexão -->
    <div class="bg-slate-800 border border-slate-700 rounded p-6 space-y-4">
      <h3 class="text-lg font-bold text-slate-100 font-mono">Status da Conexão</h3>
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <span class="text-sm text-slate-400 font-mono">WebSocket</span>
          <div class="flex items-center gap-2">
            <div 
              :class="[
                'w-3 h-3 rounded-full',
                wsConnected ? 'bg-green-500' : 'bg-red-500'
              ]"
            />
            <span :class="['text-sm font-mono', wsConnected ? 'text-green-400' : 'text-red-400']">
              {{ wsConnected ? 'Conectado' : 'Desconectado' }}
            </span>
          </div>
        </div>
        <div class="flex items-center justify-between">
          <span class="text-sm text-slate-400 font-mono">Última Mensagem</span>
          <span class="text-sm text-slate-300 font-mono">{{ lastMessageTime }}</span>
        </div>
      </div>
    </div>
    
    <!-- Seção: Log de Eventos -->
    <div class="bg-slate-800 border border-slate-700 rounded p-6 space-y-4">
      <h3 class="text-lg font-bold text-slate-100 font-mono">Log de Eventos</h3>
      <div class="bg-slate-900 rounded p-4 h-48 overflow-y-auto font-mono text-xs space-y-1">
        <div 
          v-if="eventLog.length === 0"
          class="text-slate-500"
        >
          Nenhum evento registrado
        </div>
        <div 
          v-for="(event, index) in eventLog" 
          :key="index"
          :class="[
            'text-slate-400',
            event.type === 'command' ? 'text-blue-400' : 'text-green-400'
          ]"
        >
          [{{ event.time }}] {{ event.message }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface LogEvent {
  time: string
  message: string
  type: 'command' | 'system'
}

const props = defineProps<{
  clientId: string
  wsConnected: boolean
}>()

const emit = defineEmits<{
  'send-command': [target: string]
}>()

const copied = ref(false)
const eventLog = ref<LogEvent[]>([])
const lastMessageTime = ref('--:--:--')

const copyToClipboard = async () => {
  try {
    await navigator.clipboard.writeText(props.clientId)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
    addEvent('ID copiado para a área de transferência', 'system')
  } catch (error) {
    console.error('Erro ao copiar:', error)
  }
}

const sendCommand = (target: string) => {
  // Enviar comando via WebSocket
  emit('send-command', target)
  addEvent(`Comando enviado: ${target}`, 'command')
  updateLastMessageTime()
}

const addEvent = (message: string, type: 'command' | 'system' = 'system') => {
  const now = new Date()
  const time = now.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
  
  eventLog.value.unshift({
    time,
    message,
    type
  })
  
  // Manter apenas os últimos 20 eventos
  if (eventLog.value.length > 20) {
    eventLog.value.pop()
  }
}

const updateLastMessageTime = () => {
  const now = new Date()
  lastMessageTime.value = now.toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Inicializar com um evento
addEvent('Dashboard inicializado', 'system')
updateLastMessageTime()
</script>

<style scoped>
/* Estilos específicos da view */
</style>
