<template>
  <div class="p-6 space-y-6">
    <!-- Título -->
    <div>
      <h2 class="text-2xl font-bold text-slate-100 font-mono">Projetos de TI</h2>
      <p class="text-sm text-slate-400 mt-1">Acompanhamento de projetos em andamento</p>
    </div>
    
    <!-- Grid de Projetos -->
    <div class="grid grid-cols-3 gap-6">
      <div 
        v-for="project in projects" 
        :key="project.id"
        class="bg-slate-800 border border-slate-700 rounded p-6 space-y-4"
      >
        <!-- Título do Projeto -->
        <div>
          <h3 class="text-lg font-bold text-slate-100 font-mono">{{ project.nome_projeto }}</h3>
          <p class="text-xs text-slate-400 mt-1">Responsável: {{ project.responsavel }}</p>
        </div>
        
        <!-- Status -->
        <div class="flex items-center gap-2">
          <div 
            :class="[
              'w-3 h-3 rounded-full'
            ]"
            :style="{ backgroundColor: project.cor_estado }"
          />
          <span class="text-sm font-mono text-slate-300">{{ project.estado }}</span>
        </div>
        
        <!-- Métricas -->
        <div class="space-y-3 border-t border-slate-700 pt-4">
          <div class="flex justify-between items-center">
            <span class="text-sm text-slate-400 font-mono">Tarefas Concluídas</span>
            <span class="text-2xl font-bold font-mono" style="color: var(--status-1);">{{ project.tarefas_concluidas }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-slate-400 font-mono">Em Progresso</span>
            <span class="text-2xl font-bold font-mono" style="color: var(--urgency-3);">{{ project.tarefas_em_andamento }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-slate-400 font-mono">Pendentes</span>
            <span class="text-2xl font-bold font-mono" style="color: var(--urgency-4);">{{ project.tarefas_pendentes }}</span>
          </div>
        </div>
        
        <!-- Barra de Progresso -->
        <div class="mt-4 pt-4 border-t border-slate-700">
          <div class="flex justify-between items-center mb-2">
            <span class="text-xs text-slate-400 font-mono">Progresso Geral</span>
            <span class="text-sm font-bold text-slate-300 font-mono">{{ project.progresso_geral_projeto }}%</span>
          </div>
          <div class="w-full bg-slate-900 rounded h-2 overflow-hidden">
            <div 
              :style="{ width: `${project.progresso_geral_projeto}%`, backgroundColor: 'var(--status-1)' }"
              class="h-full transition-all duration-300"
            />
          </div>
        </div>
        
        <!-- Data de Conclusão Prevista -->
        <div class="text-xs text-slate-400 font-mono pt-2">
          Previsão: {{ formatDate(project.data_entrega_vigente) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'

interface Project {
  // Adicionado um ID único para o :key do v-for
  id: string; 
  nome_projeto: string
  estado: string
  cor_estado: string
  responsavel: string
  tarefas_concluidas: number
  tarefas_em_andamento: number
  tarefas_pendentes: number
  progresso_geral_projeto: number
  data_entrega_vigente: string
}

const projects = ref<Project[]>([])
const { lastMessage, requestDataRefresh } = useWebSocket()

watch(lastMessage, (message) => {
  if (message && message.type === 'projects_update' && message.data) {
    projects.value = (message.data as any[]).map((p: any, index: number) => ({
      ...p,
      id: `${p.nome_projeto}-${index}`, // Cria um ID único
      tarefas_concluidas: parseInt(p.tarefas_concluidas, 10) || 0,
      tarefas_em_andamento: parseInt(p.tarefas_em_andamento, 10) || 0,
      tarefas_pendentes: parseInt(p.tarefas_pendentes, 10) || 0,
      progresso_geral_projeto: parseInt(p.progresso_geral_projeto, 10) || 0,
    }))
  }
})

onMounted(() => {
  requestDataRefresh('projects')
})

const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return 'N/A'
    // Adiciona um dia para corrigir o problema de fuso horário
    date.setDate(date.getDate() + 1);
    return date.toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    })
}
</script>

<style scoped>
/* Estilos específicos da view */
</style>
