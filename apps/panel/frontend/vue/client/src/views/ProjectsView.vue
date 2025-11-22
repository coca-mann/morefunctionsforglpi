<template>
  <div class="p-6 space-y-6">
    <!-- Título, Gráfico e Legenda de Status -->
    <div class="flex justify-between items-center bg-slate-800 border border-slate-700 rounded p-4">
      <!-- Título -->
      <div>
        <h2 class="text-2xl font-bold text-slate-100 font-mono">Projetos de TI</h2>
        <p class="text-sm text-slate-400 mt-1">Acompanhamento de projetos em andamento</p>
      </div>

      <!-- Gráfico Geral Compacto -->
      <div class="h-24 w-24">
        <ProjectStatusOverviewChart :projects="projects" />
      </div>

      <!-- Legenda de Status -->
      <div class="flex flex-col items-end gap-1">
        <h4 class="text-sm font-bold text-slate-300 mb-1">Legenda de Status</h4>
        <div v-for="status in projectStatuses" :key="status.name" class="flex items-center gap-2">
          <span class="text-sm text-slate-400 font-mono">{{ status.name }}</span>
          <div class="w-3 h-3 rounded-full" :style="{ backgroundColor: status.color }"></div>
        </div>
      </div>
    </div>
    
    <!-- Grid de Projetos -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="project in projects" 
        :key="project.id"
        class="relative bg-slate-800 border border-slate-700 rounded p-6"
      >
        <!-- Status (Ícone no Canto) -->
        <div 
          class="absolute top-6 right-6 w-3.5 h-3.5 rounded-full"
          :style="{ backgroundColor: project.cor_estado }"
          :title="project.estado"
        ></div>

        <!-- Conteúdo do Card com Espaçamento Vertical -->
        <div class="flex flex-col h-full space-y-6">

          <!-- Título do Projeto -->
          <div>
            <h3 class="text-lg font-bold text-slate-100 font-mono pr-6">{{ project.nome_projeto }}</h3>
            <p class="text-xs text-slate-400 mt-1">Responsável: {{ project.responsavel }}</p>
          </div>
          
          <!-- Métricas (Gráfico de Rosca) -->
          <div class="border-t border-slate-700 pt-6">
            <div v-if="project.tarefas_concluidas + project.tarefas_em_andamento + project.tarefas_pendentes > 0">
              <ProjectTaskDistributionChart 
                :completed="project.tarefas_concluidas"
                :in-progress="project.tarefas_em_andamento"
                :pending="project.tarefas_pendentes"
              />
            </div>
            <div v-else class="h-32 flex items-center justify-center">
                <p class="text-sm text-slate-500 font-mono">Nenhuma tarefa neste projeto.</p>
            </div>
          </div>
          
          <!-- Barra de Progresso -->
          <div class="pt-6 border-t border-slate-700">
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
          <div class="flex-grow flex items-end justify-center">
            <div class="text-xs font-mono pt-4 text-center" :class="getUrgencyInfo(project.data_entrega_vigente).cssClass">
              {{ getUrgencyInfo(project.data_entrega_vigente).text }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useWebSocket } from '../composables/useWebSocket'
import ProjectStatusOverviewChart from '@/components/ProjectStatusOverviewChart.vue';
import ProjectTaskDistributionChart from '@/components/ProjectTaskDistributionChart.vue';

interface Project {
  // Adicionado um ID único para o :key do v-for
  id: string; 
  nome_projeto: string;
  estado: string;
  cor_estado: string;
  responsavel: string;
  tarefas_concluidas: number;
  tarefas_em_andamento: number;
  tarefas_pendentes: number;
  progresso_geral_projeto: number;
  data_entrega_vigente: string;
}

// Define a estrutura da mensagem do WebSocket para atualização de projetos
interface ProjectsUpdateMessage {
  type: 'projects_update';
  data: Omit<Project, 'id'>[]; // O 'id' é gerado no frontend
}


const projects = ref<Project[]>([])
const { lastMessage, requestDataRefresh } = useWebSocket()

// Computa os status únicos para a legenda
const projectStatuses = computed(() => {
  const statuses = new Map<string, string>();
  for (const project of projects.value) {
    if (!statuses.has(project.estado)) {
      statuses.set(project.estado, project.cor_estado);
    }
  }
  return Array.from(statuses, ([name, color]) => ({ name, color }));
});

watch(lastMessage, (message: ProjectsUpdateMessage) => {
  if (message && message.type === 'projects_update' && message.data) {
    projects.value = message.data.map((p, index) => ({
      ...p,
      id: `${p.nome_projeto}-${index}`, // Cria um ID único
      tarefas_concluidas: parseInt(p.tarefas_concluidas as any, 10) || 0,
      tarefas_em_andamento: parseInt(p.tarefas_em_andamento as any, 10) || 0,
      tarefas_pendentes: parseInt(p.tarefas_pendentes as any, 10) || 0,
      progresso_geral_projeto: parseInt(p.progresso_geral_projeto as any, 10) || 0,
    }))
  }
})

onMounted(() => {
  requestDataRefresh('projects')
})

const getUrgencyInfo = (dateStr: string | null): { text: string; cssClass: string } => {
  if (!dateStr) {
    return { text: 'Previsão: N/A', cssClass: 'text-slate-500' };
  }
  
  const today = new Date();
  today.setHours(0, 0, 0, 0); // Normaliza para o início do dia

  const dueDate = new Date(dateStr);
  if (isNaN(dueDate.getTime())) {
      return { text: 'Data Inválida', cssClass: 'text-slate-500' };
  }
  dueDate.setHours(0,0,0,0); // Normaliza a data de entrega

  const diffTime = dueDate.getTime() - today.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return { text: `Atrasado em ${Math.abs(diffDays)} dia(s)`, cssClass: 'text-red-400 font-bold' };
  }
  if (diffDays === 0) {
    return { text: `Entrega hoje!`, cssClass: 'text-yellow-400 font-bold' };
  }
  if (diffDays <= 7) {
    return { text: `Entrega em ${diffDays} dia(s)`, cssClass: 'text-yellow-400' };
  }
  
  const formattedDate = dueDate.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' });
  return { text: `Previsão: ${formattedDate}`, cssClass: 'text-slate-400' };
}
</script>

<style scoped>
/* Estilos específicos da view */
</style>
