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
            <th class="px-4 py-3 text-center text-slate-300">Status</th>
            <th class="px-4 py-3 text-center text-slate-300">Abertura</th>
            <th class="px-4 py-3 text-center text-slate-300">Entidade</th>
            <th class="px-4 py-3 text-left text-slate-300">Título</th>
            <th class="px-4 py-3 text-center text-slate-300">Urgência</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ticket in tickets" :key="ticket.id"
            class="border-b border-slate-700 hover:bg-slate-700 transition-colors">
            <td class="px-4 py-3 text-center">
              <span class="px-3 py-1 rounded font-bold text-xs whitespace-nowrap" :style="getStatusStyle(ticket.idstatus)">
                {{ ticket.status }}
              </span>
            </td>
            <td class="px-4 py-3 text-slate-300 text-center text-xs">
              <div>{{ ticket.abertura ? ticket.abertura.split(' ')[0] : '-' }}</div>
              <div>{{ ticket.abertura ? ticket.abertura.split(' ')[1] : '-' }}</div>
            </td>
            <td class="px-4 py-3 text-slate-300 text-center">{{ ticket.entidade }}</td>
            <td class="px-4 py-3 text-slate-200">{{ ticket.titulo }}</td>
            <td class="px-4 py-3 text-center">
              <span class="px-3 py-1 rounded font-bold text-xs whitespace-nowrap" :style="getUrgencyStyle(ticket.urgencia)">
                {{ ticket.urgencia }}
              </span>
            </td>
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
  id: string;
  titulo: string;
  entidade: string;
  abertura: string;
  status: string;
  urgencia: string;
  idstatus: number;
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
    // Backend fields: id, Entidade, Titulo, Abertura, Status, Urgencia, idstatus
    return {
      id: String(item.id),
      titulo: item.Titulo,
      entidade: item.Entidade,
      abertura: item.Abertura,
      status: item.Status,
      urgencia: item.Urgencia,
      idstatus: item.idstatus
    }
  })
}

onMounted(() => {
  // Request data when component mounts
  requestDataRefresh('tickets')
})

const getStatusStyle = (statusId: number) => {
  const styles: Record<number, Record<string, string>> = {
    1: { // Novo
      backgroundColor: 'var(--status-1)',
      color: 'var(--status-1-text)',
      border: 'none',
    },
    2: { // Em atendimento
      backgroundColor: 'transparent',
      color: 'var(--status-2-border)',
      border: '1px solid var(--status-2-border)',
    },
    3: { // Em atendimento (planejado)
      backgroundColor: 'transparent',
      color: 'var(--status-3-border)',
      border: '1px solid var(--status-3-border)',
    },
    4: { // Pendente
      backgroundColor: 'var(--status-4)',
      color: 'var(--status-4-text)',
      border: 'none',
    },
    5: { // Solucionado
      backgroundColor: 'var(--status-5)',
      color: 'var(--status-5-text)',
      border: 'none',
    },
    6: { // Fechado
      backgroundColor: 'var(--status-5)',
      color: 'var(--status-5-text)',
      border: 'none',
    },
    10: { // Aprovação
      backgroundColor: 'var(--status-10)',
      color: 'var(--status-10-text)',
      border: 'none',
    }
  };
  return styles[statusId] || { backgroundColor: '#slate-600', color: 'white' };
}

const getUrgencyStyle = (urgencyText: string) => {
  const styles: Record<string, Record<string, string>> = {
    'Muito Alta': {
      backgroundColor: 'transparent',
      color: 'var(--urgency-5)',
      border: '1px solid var(--urgency-5)',
    },
    'Alta': {
      backgroundColor: 'transparent',
      color: 'var(--urgency-4)',
      border: '1px solid var(--urgency-4)',
    },
    'Média': {
      backgroundColor: 'transparent',
      color: 'var(--urgency-3)',
      border: '1px solid var(--urgency-3)',
    },
    'Baixa': {
      backgroundColor: 'transparent',
      color: 'var(--urgency-2)',
      border: '1px solid var(--urgency-2)',
    },
    'Muito baixa': {
      backgroundColor: 'transparent',
      color: 'var(--urgency-1)',
      border: '1px solid var(--urgency-1)',
    },
  };
  return styles[urgencyText] || { border: '1px solid gray', color: 'gray' };
}

const criticalCount = computed(() => tickets.value.filter(t => t.urgencia === 'Muito Alta').length)
const highCount = computed(() => tickets.value.filter(t => t.urgencia === 'Alta').length)
const mediumCount = computed(() => tickets.value.filter(t => t.urgencia === 'Média').length)
const lowCount = computed(() => tickets.value.filter(t => t.urgencia === 'Baixa' || t.urgencia === 'Muito baixa').length)

</script>

<style scoped>
/* Estilos específicos da view */
</style>
