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
          <h3 class="text-lg font-bold text-slate-100 font-mono">{{ project.name }}</h3>
          <p class="text-xs text-slate-400 mt-1">Responsável: {{ project.responsible }}</p>
        </div>
        
        <!-- Status -->
        <div class="flex items-center gap-2">
          <div 
            :class="[
              'w-3 h-3 rounded-full'
            ]"
            :style="{ backgroundColor: getStatusColor(project.status) }"
          />
          <span class="text-sm font-mono text-slate-300">{{ statusLabels[project.status] }}</span>
        </div>
        
        <!-- Métricas -->
        <div class="space-y-3 border-t border-slate-700 pt-4">
          <div class="flex justify-between items-center">
            <span class="text-sm text-slate-400 font-mono">Tarefas Concluídas</span>
            <span class="text-2xl font-bold font-mono" style="color: var(--status-1);">{{ project.completed }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-slate-400 font-mono">Em Progresso</span>
            <span class="text-2xl font-bold font-mono" style="color: var(--urgency-3);">{{ project.inProgress }}</span>
          </div>
          <div class="flex justify-between items-center">
            <span class="text-sm text-slate-400 font-mono">Pendentes</span>
            <span class="text-2xl font-bold font-mono" style="color: var(--urgency-4);">{{ project.pending }}</span>
          </div>
        </div>
        
        <!-- Barra de Progresso -->
        <div class="mt-4 pt-4 border-t border-slate-700">
          <div class="flex justify-between items-center mb-2">
            <span class="text-xs text-slate-400 font-mono">Progresso Geral</span>
            <span class="text-sm font-bold text-slate-300 font-mono">{{ project.progress }}%</span>
          </div>
          <div class="w-full bg-slate-900 rounded h-2 overflow-hidden">
            <div 
              :style="{ width: `${project.progress}%`, backgroundColor: 'var(--status-1)' }"
              class="h-full transition-all duration-300"
            />
          </div>
        </div>
        
        <!-- Data de Conclusão Prevista -->
        <div class="text-xs text-slate-400 font-mono pt-2">
          Previsão: {{ project.dueDate }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Project {
  id: string
  name: string
  responsible: string
  status: 'planning' | 'in_progress' | 'testing' | 'completed'
  completed: number
  inProgress: number
  pending: number
  progress: number
  dueDate: string
}

const projects: Project[] = [
  {
    id: '1',
    name: 'Migração para Cloud',
    responsible: 'Ana Oliveira',
    status: 'in_progress',
    completed: 45,
    inProgress: 12,
    pending: 8,
    progress: 82,
    dueDate: '15/12/2025'
  },
  {
    id: '2',
    name: 'Implementação VoIP',
    responsible: 'Carlos Mendes',
    status: 'planning',
    completed: 8,
    inProgress: 5,
    pending: 20,
    progress: 28,
    dueDate: '30/01/2026'
  },
  {
    id: '3',
    name: 'Upgrade Infraestrutura',
    responsible: 'Pedro Costa',
    status: 'testing',
    completed: 52,
    inProgress: 8,
    pending: 3,
    progress: 94,
    dueDate: '22/11/2025'
  }
]

const statusLabels: Record<string, string> = {
  planning: 'PLANEJAMENTO',
  in_progress: 'EM ANDAMENTO',
  testing: 'TESTES',
  completed: 'CONCLUÍDO'
}

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    planning: 'var(--color-scrollbar-thumb)',
    in_progress: 'var(--urgency-3)',
    testing: 'var(--status-3-border)',
    completed: 'var(--status-1)'
  }
  return colors[status] || 'var(--color-scrollbar-thumb)'
}
</script>

<style scoped>
/* Estilos específicos da view */
</style>
