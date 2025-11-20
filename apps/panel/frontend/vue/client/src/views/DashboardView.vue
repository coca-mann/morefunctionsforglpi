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
        <div class="text-sm text-slate-400 font-mono">Tickets Abertos Hoje</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--status-3-border);">{{ openTickets }}</div>
        <div class="text-xs mt-2" :class="getDifferenceClass(differenceSinceYesterday)">
          <span v-if="differenceSinceYesterday > 0">↑</span>
          <span v-else-if="differenceSinceYesterday < 0">↓</span>
          <span v-else>~</span>
          {{ Math.abs(differenceSinceYesterday) }} desde ontem
        </div>
      </div>

      <div class="bg-slate-800 border border-slate-700 rounded p-4">
        <div class="text-sm text-slate-400 font-mono">Tempo Médio Solução</div>
        <div class="text-3xl font-bold font-mono mt-2" style="color: var(--status-1);">{{ avgResponseTime }}</div>
        <div class="text-xs mt-2" :class="getResponseTimeDiffClass(avgResponseTimeDiff)">
          <span v-if="avgResponseTimeDiff > 0">↑</span>
          <span v-else-if="avgResponseTimeDiff < 0">↓</span>
          <span v-else>~</span>
          {{ formatDiffTime(avgResponseTimeDiff) }} vs mês passado
        </div>
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
      <!-- Técnicos de Manutenção -->
      <div class="bg-slate-800 border border-slate-700 rounded p-6">
        <h3 class="text-lg font-bold text-slate-100 font-mono mb-4">Técnicos de Manutenção</h3>
        <div class="space-y-3">
          <div v-for="tech in technicians" :key="tech.login"
            class="flex flex-col p-3 bg-slate-900 rounded">
            <div class="text-base font-bold font-mono text-slate-100 mb-2">{{ tech.nome_completo }}</div>
            <div class="text-xs text-slate-400 flex justify-around">
              <div>Tickets: <strong class="text-blue-400">{{ tech.qtd_tickets_atribuidos }}</strong></div>
              <div>Projetos: <strong class="text-blue-400">{{ tech.qtd_projetos_relacionados }}</strong></div>
              <div>Tarefas: <strong class="text-blue-400">{{ tech.qtd_total_tarefas }}</strong></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Analistas de Sistemas -->
      <div class="bg-slate-800 border border-slate-700 rounded p-6">
        <h3 class="text-lg font-bold text-slate-100 font-mono mb-4">Analistas de Sistemas</h3>
        <div class="space-y-3">
          <div v-for="analyst in analysts" :key="analyst.login"
            class="flex flex-col p-3 bg-slate-900 rounded">
            <div class="text-base font-bold font-mono text-slate-100 mb-2">{{ analyst.nome_completo }}</div>
            <div class="text-xs text-slate-400 flex justify-around">
              <div>Tickets: <strong class="text-blue-400">{{ analyst.qtd_tickets_atribuidos }}</strong></div>
              <div>Projetos: <strong class="text-blue-400">{{ analyst.qtd_projetos_relacionados }}</strong></div>
              <div>Tarefas: <strong class="text-blue-400">{{ analyst.qtd_total_tarefas }}</strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Atividade Recente -->
    <div v-if="false" class="bg-slate-800 border border-slate-700 rounded p-6">
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

interface TeamMember {
  nome_completo: string
  login: string
  grupo_perfil: 'Analistas' | 'Técnicos'
  qtd_tickets_atribuidos: number
  qtd_projetos_relacionados: number
  qtd_total_tarefas: number
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
const differenceSinceYesterday = ref(0)
const avgResponseTime = ref('0h 0m')
const avgResponseTimeDiff = ref(0)
const resolvedToday = ref(0)
const customerSatisfaction = ref(0)
const surveyCount = ref(0)
const technicians = ref<TeamMember[]>([])
const analysts = ref<TeamMember[]>([])

// Watch for WebSocket messages
watch(lastMessage, (message) => {
  // Handle new dashboard-specific KPI updates
  if (message && message.type === 'dashboard_update' && message.kpis) {
    openTickets.value = message.kpis.total_hoje ?? 0
    differenceSinceYesterday.value = message.kpis.diferenca ?? 0
    avgResponseTime.value = formatResponseTime(message.kpis.solucao_mes_atual)
    avgResponseTimeDiff.value = parseFloat(message.kpis.diferenca_segundos) || 0
    resolvedToday.value = message.kpis.resolved_today ?? 0
    customerSatisfaction.value = Math.round(parseFloat(message.kpis.porcentagem_satisfacao)) || 0
    surveyCount.value = message.kpis.qtd_pesquisas_respondidas ?? 0

    if (message.kpis.team_members) {
      technicians.value = message.kpis.team_members.filter((m: TeamMember) => m.grupo_perfil === 'Técnicos');
      analysts.value = message.kpis.team_members.filter((m: TeamMember) => m.grupo_perfil === 'Analistas');
    }
  }

  // Handle updates from the general ticket poll
  if (message && message.type === 'tickets_update' && message.counters) {
    // This could be deprecated if dashboard_update provides all KPIs
    // resolvedToday.value = message.counters.resolved_today // Removed, now handled by dashboard_update
  }
})

onMounted(() => {
  requestDataRefresh('dashboard')
})

const getDifferenceClass = (diff: number) => {
  if (diff > 0) return 'text-red-500' // More tickets is bad
  if (diff < 0) return 'text-green-500' // Fewer tickets is good
  return 'text-slate-500' // No change
}

const formatResponseTime = (timeStr: string | null) => {
  if (!timeStr) return 'N/A'
  const parts = timeStr.split(':')
  if (parts.length < 2) return 'N/A'
  const hours = parseInt(parts[0], 10)
  const minutes = parseInt(parts[1], 10)
  if (isNaN(hours) || isNaN(minutes)) return 'N/A'
  return `${hours}h ${minutes}m`
}

// Format difference in seconds to "X min"
const formatDiffTime = (seconds: number | null) => {
  if (seconds === null || isNaN(seconds)) return '0 min'
  const totalMinutes = Math.round(Math.abs(seconds) / 60)

  if (totalMinutes === 0) return '0 min'

  if (totalMinutes < 60) {
    return `${totalMinutes} min`
  } else {
    const hours = Math.floor(totalMinutes / 60)
    const remainingMinutes = totalMinutes % 60
    if (remainingMinutes === 0) {
      return `${hours}h`
    } else {
      return `${hours}h ${remainingMinutes}m`
    }
  }
}

// Get class for the difference (lower is better)
const getResponseTimeDiffClass = (diff: number | null) => {
  if (diff === null || isNaN(diff)) return 'text-slate-500'
  if (diff > 0) return 'text-red-500' // Higher time is bad
  if (diff < 0) return 'text-green-500' // Lower time is good
  return 'text-slate-500'
}

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
