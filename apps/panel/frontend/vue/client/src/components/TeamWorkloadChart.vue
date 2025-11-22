<template>
  <div class="space-y-4">
    <h3 class="text-lg font-bold text-slate-100 font-mono">{{ title }}</h3>
    <div v-if="chartData && chartData.datasets[0] && chartData.datasets[0].data.length > 0" class="h-64">
      <Bar
        :chart-data="chartData"
        :chart-options="chartOptions"
        chart-id="my-chart-id"
        dataset-id-key="label"
        class="w-full h-full"
      />
    </div>
    <div v-else class="text-slate-400 text-center py-10">
      Carregando dados do gráfico ou nenhum membro da equipe encontrado.
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Bar } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import type { ChartData, ChartOptions } from 'chart.js'; // Import directly from chart.js

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
  ChartDataLabels
);

interface TeamMember {
  nome_completo: string;
  qtd_tickets_atribuidos: number;
  qtd_projetos_relacionados: number;
  qtd_total_tarefas: number;
}

const props = defineProps<{
  title: string;
  members: TeamMember[];
}>();

const chartData = computed<ChartData<'bar'>>(() => {
  if (!props.members || props.members.length === 0) {
    return {
      labels: [],
      datasets: []
    };
  }
  const labels = props.members.map(m => m.nome_completo);
  return {
    labels,
    datasets: [
      {
        label: 'Tickets',
        data: props.members.map(m => m.qtd_tickets_atribuidos),
        backgroundColor: 'rgba(59, 130, 246, 0.7)', // Slightly more opaque
        borderColor: 'rgb(59, 130, 246)',
        borderWidth: 1,
      },
      {
        label: 'Projetos',
        data: props.members.map(m => m.qtd_projetos_relacionados),
        backgroundColor: 'rgba(34, 197, 94, 0.7)', // Slightly more opaque
        borderColor: 'rgb(34, 197, 94)',
        borderWidth: 1,
      },
      {
        label: 'Tarefas',
        data: props.members.map(m => m.qtd_total_tarefas),
        backgroundColor: 'rgba(234, 76, 60, 0.7)', // Slightly more opaque
        borderColor: 'rgb(234, 76, 60)',
        borderWidth: 1,
      },
    ],
  };
});

const chartOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: '#94a3b8', // slate-400
        font: {
            family: 'monospace'
        }
      },
    },
    tooltip: {
        bodyFont: {
            family: 'monospace'
        },
        titleFont: {
            family: 'monospace'
        }
    },
    datalabels: {
      color: '#fff',
      anchor: 'end',
      align: 'start',
      offset: -4,
      font: {
        family: 'monospace',
        weight: 'bold'
      },
      formatter: (value) => {
        // Only show value if it's greater than 0
        return value > 0 ? value : '';
      }
    }
  },
  scales: {
    x: {
      stacked: false, // Ensure bars are grouped, not stacked
      ticks: {
        color: '#94a3b8',
         font: {
            family: 'monospace'
        }
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
    y: {
      stacked: false, // Ensure bars are grouped, not stacked
      beginAtZero: true,
      ticks: {
        color: '#94a3b8',
         font: {
            family: 'monospace'
        },
        stepSize: 1
      },
      grid: {
        color: 'rgba(255, 255, 255, 0.1)',
      },
    },
  },
}));
</script>
