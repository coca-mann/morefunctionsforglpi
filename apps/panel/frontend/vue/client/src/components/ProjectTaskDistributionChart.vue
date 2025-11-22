<template>
  <div class="relative h-32 w-32 mx-auto">
    <Doughnut
      :chart-data="chartData"
      :chart-options="chartOptions"
      chart-id="task-distribution-chart"
    />
    <div class="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span class="text-2xl font-bold font-mono text-slate-100">{{ totalTasks }}</span>
        <span class="text-xs text-slate-400">Tarefas</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Doughnut } from 'vue-chartjs';
import { Chart as ChartJS, ArcElement, Tooltip } from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import type { ChartData, ChartOptions } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, ChartDataLabels);

const props = defineProps<{
  completed: number;
  inProgress: number;
  pending: number;
}>();

const totalTasks = computed(() => props.completed + props.inProgress + props.pending);

const chartData = computed<ChartData<'doughnut'>>(() => ({
  labels: ['Concluídas', 'Em Andamento', 'Pendentes'],
  datasets: [
    {
      data: [props.completed, props.inProgress, props.pending],
      backgroundColor: [
        'rgba(34, 197, 94, 0.9)',    // Verde (Concluído)
        'rgba(234, 179, 8, 0.9)',    // Amarelo (Em Andamento)
        'rgba(239, 68, 68, 0.9)',     // Vermelho (Pendente)
      ],
      borderColor: '#334155', // slate-700
      borderWidth: 2,
      hoverOffset: 4,
    },
  ],
}));

const chartOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  aspectRatio: 1,
  cutout: '60%', // Aumentar a espessura do doughnut para melhor visualização dos labels
  animation: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      enabled: true,
       bodyFont: {
          family: 'monospace'
      },
      titleFont: {
          family: 'monospace'
      }
    },
    datalabels: {
        display: true, // Ativar exibição dos rótulos
        color: '#fff', // Cor do texto
        font: {
            family: 'monospace',
            weight: 'bold',
            size: 14, // Aumentar o tamanho da fonte
        },
        formatter: (value) => {
            return value > 0 ? value : ''; // Exibir apenas valores maiores que 0
        },
    },
  },
}));
</script>
