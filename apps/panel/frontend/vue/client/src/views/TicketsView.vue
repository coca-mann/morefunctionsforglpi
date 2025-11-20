<template>
  <div class="p-6 space-y-6">
    <!-- Título -->
    <div>
      <h2 class="text-2xl font-bold text-slate-100 font-mono">Tickets de Manutenção</h2>
      <p class="text-sm text-slate-400 mt-1">Total: {{ tickets.length }} tickets abertos</p>
    </div>
    
    <!-- Contadores de Topo -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">CRÍTICO</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--urgency-5);">
          {{ criticalCount }}
        </div>
      </div>
      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">ALTO</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--urgency-4);">
          {{ highCount }}
        </div>
      </div>
      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">MÉDIO</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--urgency-3);">
          {{ mediumCount }}
        </div>
      </div>
      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">BAIXO</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--urgency-1);">
          {{ lowCount }}
        </div>
      </div>
    </div>
    
    <!-- Tabela de Tickets -->
    <div class="bg-slate-800 border border-slate-700 rounded overflow-hidden">
      <table class="w-full text-sm font-mono">
        <thead class="bg-slate-900 border-b border-slate-700">
          <tr>
            <th class="px-4 py-3 text-left text-slate-300">ID</th>
            <th class="px-4 py-3 text-left text-slate-300">Descrição</th>
            <th class="px-4 py-3 text-left text-slate-300">Atribuído a</th>
            <th class="px-4 py-3 text-left text-slate-300">Prioridade</th>
            <th class="px-4 py-3 text-left text-slate-300">Status</th>
            <th class="px-4 py-3 text-left text-slate-300">Tempo Decorrido</th>
          </tr>
        </thead>
        <tbody>
          <tr 
            v-for="ticket in tickets" 
            :key="ticket.id"
            class="border-b border-slate-700 hover:bg-slate-700 transition-colors"
          >
            <td class="px-4 py-3 text-slate-300 font-bold">#{{ ticket.id }}</td>
            <td class="px-4 py-3 text-slate-200">{{ ticket.description }}</td>
            <td class="px-4 py-3 text-slate-300">{{ ticket.assignedTo }}</td>
            <td class="px-4 py-3">
              <span 
                class="px-2 py-1 rounded text-xs font-bold border"
                :style="getPriorityStyle(ticket.priority)"
              >
                {{ priorityLabels[ticket.priority] }}
              </span>
            </td>
            <td class="px-4 py-3">
              <span 
                :class="[
                  'px-2 py-1 rounded text-xs font-bold',
                  ticket.status === 'open' ? 'bg-blue-900 text-blue-300' : 'bg-green-900 text-green-300'
                ]"
              >
                {{ ticket.status === 'open' ? 'ABERTO' : 'FECHADO' }}
              </span>
            </td>
            <td class="px-4 py-3 text-slate-300">{{ formatElapsedTime(ticket.createdAt) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'

interface Ticket {
  id: string
  description: string
  assignedTo: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  status: 'open' | 'closed'
  createdAt: string
}

const tickets = ref<Ticket[]>([])
const { lastMessage, requestDataRefresh } = useWebSocket()

// Watch for WebSocket messages
watch(lastMessage, (message) => {
  if (message && message.type === 'tickets_update' && message.data) {
    handleTicketsUpdate(message.data)
  }
})

const handleTicketsUpdate = (data: any[]) => {
  tickets.value = data.map((item: any) => {
    // Map backend fields to frontend interface
    // Backend: id, Entidade, Titulo, Abertura, Status, Urgencia, Solicitante, Tecnico, idstatus
    
    let priority: Ticket['priority'] = 'low'
    if (item.Urgencia === 'Muito Alta') priority = 'critical'
    else if (item.Urgencia === 'Alta') priority = 'high'
    else if (item.Urgencia === 'Média') priority = 'medium'
    
    // Map Status. 5 is Solucionado (Closed), others Open
    // idstatus: 1=Novo, 2=Em atendimento, 3=Planejado, 4=Pendente, 5=Solucionado, 6=Fechado
    const status: Ticket['status'] = (item.idstatus === 5 || item.idstatus === 6) ? 'closed' : 'open'

    // Parse date 'dd/mm/yy HH:MM' to ISO for sorting/display
    // Note: Assuming current year/century if needed, but string format might be enough for display if not calculating time.
    // But formatElapsedTime needs a Date object.
    // Let's try to parse it manually.
    const [datePart, timePart] = item.Abertura.split(' ')
    const [day, month, year] = datePart.split('/')
    const [hour, minute] = timePart.split(':')
    // Assuming 20xx for year
    const isoDate = `20${year}-${month}-${day}T${hour}:${minute}:00`

    return {
      id: String(item.id),
      description: item.Titulo,
      assignedTo: item.Tecnico || 'Não atribuído',
      priority: priority,
      status: status,
      createdAt: isoDate
    }
  })
}

onMounted(() => {
  // Request data when component mounts
  requestDataRefresh('tickets')
})

const priorityLabels: Record<string, string> = {
  critical: 'CRÍTICO',
  high: 'ALTO',
  medium: 'MÉDIO',
  low: 'BAIXO'
}

const getPriorityStyle = (priority: string) => {
  const styles: Record<string, Record<string, string>> = {
    critical: {
      borderColor: 'var(--urgency-5)',
      backgroundColor: 'rgba(105, 58, 182, 0.1)',
      color: 'var(--urgency-5)'
    },
    high: {
      borderColor: 'var(--urgency-4)',
      backgroundColor: 'rgba(234, 76, 60, 0.1)',
      color: 'var(--urgency-4)'
    },
    medium: {
      borderColor: 'var(--urgency-3)',
      backgroundColor: 'rgba(247, 155, 30, 0.1)',
      color: 'var(--urgency-3)'
    },
    low: {
      borderColor: 'var(--urgency-1)',
      backgroundColor: 'rgba(87, 174, 82, 0.1)',
      color: 'var(--urgency-1)'
    }
  }
  return styles[priority] || styles.low
}

const criticalCount = computed(() => tickets.value.filter(t => t.priority === 'critical').length)
const highCount = computed(() => tickets.value.filter(t => t.priority === 'high').length)
const mediumCount = computed(() => tickets.value.filter(t => t.priority === 'medium').length)
const lowCount = computed(() => tickets.value.filter(t => t.priority === 'low').length)

const formatElapsedTime = (dateString: string) => {
  const createdDate = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - createdDate.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)
  
  if (isNaN(diffHours)) return '-'

  if (diffDays > 0) {
    return `${diffDays}d ${diffHours % 24}h`
  } else {
    return `${diffHours}h`
  }
}
</script>

<style scoped>
/* Estilos específicos da view */
</style>
