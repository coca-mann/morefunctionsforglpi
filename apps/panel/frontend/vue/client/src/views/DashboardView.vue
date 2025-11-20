<template>
  <div class="p-6 space-y-6">
    <!-- Título -->
    <div>
      <h2 class="text-2xl font-bold text-slate-100 font-mono">Dashboard de Desempenho</h2>
      <p class="text-sm text-slate-400 mt-1">Métricas e KPIs do setor de TI</p>
    </div>

    <!-- KPIs Principais -->
    <div class="grid grid-cols-4 gap-4">
      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">Tickets Abertos</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--status-3-border);">{{ openTickets }}</div>
        <div class="text-xs text-slate-500 mt-2">↑ 2 desde ontem</div>
      </div>

      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">Tempo Médio Resposta</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--status-1);">{{ avgResponseTime }}</div>
        <div class="text-xs text-slate-500 mt-2">↓ 15 min vs semana</div>
      </div>

      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">Resolvidos Hoje</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--urgency-3);">{{ resolvedToday }}</div>
        <div class="text-xs text-slate-500 mt-2">Meta: 10/dia</div>
      </div>

      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">Satisfação Cliente</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--status-10);">{{ customerSatisfaction }}%
        </div>
        <div class="text-xs text-slate-500 mt-2">Baseado em {{ surveyCount }} pesquisas</div>
      </div>
    </div>

    <!-- Equipe -->
    <div class="grid grid-cols-2 gap-6">
      <!-- Técnicos Disponíveis -->
      <div class="bg-slate-800 border border-slate-700 rounded p-6">
        <h3 class="text-lg font-bold text-slate-100 font-mono mb-4">Técnicos de Manutenção</h3>
        <div class="space-y-3">
          <div v-for="tech in technicians" :key="tech.id"
            class="flex items-center justify-between p-3 bg-slate-900 rounded">
            <div>
              <div class="text-sm font-mono text-slate-100">{{ tech.name }}</div>
              <div class="text-xs text-slate-400">{{ tech.specialization }}</div>
            </div>
            <div class="flex items-center gap-2">
              <div :class="[
                'w-3 h-3 rounded-full'
              ]" :style="{ backgroundColor: tech.available ? 'var(--status-1)' : 'var(--urgency-4)' }" />
              <span class="text-xs text-slate-400">{{ tech.ticketsAssigned }} tickets</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Analistas de Sistemas -->
      <div class="bg-slate-800 border border-slate-700 rounded p-6">
        <h3 class="text-lg font-bold text-slate-100 font-mono mb-4">Analistas de Sistemas</h3>
        <div class="space-y-3">
          <div v-for="analyst in analysts" :key="analyst.id"
            class="flex items-center justify-between p-3 bg-slate-900 rounded">
            <div>
              <div class="text-sm font-mono text-slate-100">{{ analyst.name }}</div>
              <div class="text-xs text-slate-400">{{ analyst.expertise }}</div>
            </div>
            <div class="flex items-center gap-2">
              <div :class="[
                'w-3 h-3 rounded-full'
              ]" :style="{ backgroundColor: analyst.available ? 'var(--status-1)' : 'var(--urgency-4)' }" />
              <span class="text-xs text-slate-400">{{ analyst.projectsAssigned }} projetos</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Atividade Recente -->
    <div class="bg-slate-800 border border-slate-700 rounded p-6">
      <h3 class="text-lg font-bold text-slate-100 font-mono mb-4">Atividade Recente</h3>
      <div class="space-y-2 font-mono text-sm">
        <div v-for="(activity, index) in recentActivity" :key="index"
          class="flex items-center justify-between p-2 bg-slate-900 rounded">
          <div class="flex-1">
            <span class="text-slate-400">{{ activity.time }}</span>
            <span class="text-slate-300 ml-4">{{ activity.description }}</span>
          </div>
          <span :class="['text-xs px-2 py-1 rounded']" :style="{
            backgroundColor: activity.bgColor,
            color: activity.textColor
          }">
            {{ activity.type }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'

interface Technician {
  id: string
  name: string
  specialization: string
  available: boolean
  ticketsAssigned: number
}

interface Analyst {
  id: string
  name: string
  expertise: string
  available: boolean
  projectsAssigned: number
}

interface Activity {
  time: string
  description: string
  type: string
  bgColor: string
  textColor: string
}

const { lastMessage, requestDataRefresh } = useWebSocket()

const openTickets = ref(0)
const avgResponseTime = ref('2h 30m')
const resolvedToday = ref(0)
const customerSatisfaction = ref(88)
const surveyCount = ref(47)

// Watch for WebSocket messages
watch(lastMessage, (message) => {
  if (message && message.type === 'tickets_update' && message.counters) {
    openTickets.value = message.counters.total
    resolvedToday.value = message.counters.resolved_today
    // openToday.value = message.counters.open_today // Available if needed
  }
})

onMounted(() => {
  requestDataRefresh('dashboard')
})

const technicians: Technician[] = [
  { id: '1', name: 'João Silva', specialization: 'Hardware', available: true, ticketsAssigned: 3 },
  { id: '2', name: 'Maria Santos', specialization: 'Rede', available: true, ticketsAssigned: 2 },
  { id: '3', name: 'Pedro Costa', specialization: 'Periféricos', available: false, ticketsAssigned: 4 },
  { id: '4', name: 'Ana Oliveira', specialization: 'Impressoras', available: true, ticketsAssigned: 1 }
]

const analysts: Analyst[] = [
  { id: '1', name: 'Carlos Mendes', expertise: 'Infraestrutura', available: true, projectsAssigned: 2 },
  { id: '2', name: 'Fernanda Lima', expertise: 'Banco de Dados', available: true, projectsAssigned: 1 },
  { id: '3', name: 'Roberto Alves', expertise: 'Segurança', available: false, projectsAssigned: 3 }
]

const recentActivity: Activity[] = [
  {
    time: '14:35',
    description: 'Ticket #005 atribuído a Carlos Mendes',
    type: 'ATRIBUIÇÃO',
    bgColor: 'rgba(59, 130, 246, 0.2)',
    textColor: 'var(--status-3-border)'
  },
  {
    time: '14:20',
    description: 'Projeto "Migração Cloud" progresso 82%',
    type: 'PROGRESSO',
    bgColor: 'rgba(34, 197, 94, 0.2)',
    textColor: 'var(--status-1)'
  },
  {
    time: '14:05',
    description: 'Ticket #003 fechado por Pedro Costa',
    type: 'FECHADO',
    bgColor: 'rgba(34, 197, 94, 0.2)',
    textColor: 'var(--status-1)'
  },
  {
    time: '13:50',
    description: 'Novo ticket #006 criado - Prioridade Baixa',
    type: 'NOVO',
    bgColor: 'rgba(247, 155, 30, 0.2)',
    textColor: 'var(--urgency-3)'
  },
  {
    time: '13:30',
    description: 'Ticket #001 escalado para Crítico',
    type: 'ESCALAÇÃO',
    bgColor: 'rgba(234, 76, 60, 0.2)',
    textColor: 'var(--urgency-4)'
  }
]
</script>

<style scoped>
/* Estilos específicos da view */
</style>
