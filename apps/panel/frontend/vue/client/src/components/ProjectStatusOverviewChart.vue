<template>
  <div v-if="chartData.datasets[0]?.data.length > 0" class="w-full h-full">
    <Doughnut
      :chart-data="chartData"
      :chart-options="chartOptions"
      chart-id="portfolio-overview-chart"
    />
  </div>
  <div v-else class="w-full h-full flex items-center justify-center">
    <p class="text-xs text-slate-500 text-center">Sem dados</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Doughnut } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import type { ChartData, ChartOptions } from 'chart.js';

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  ArcElement,
  ChartDataLabels
);

interface Project {
  estado: string;
  cor_estado: string;
  // Adicione outras propriedades do projeto se necessário
}

const props = defineProps<{
  projects: Project[];
}>();

const chartData = computed<ChartData<'doughnut'>>(() => {
  const statusCounts: { [key: string]: { count: number; color: string } } = {};

  for (const project of props.projects) {
    if (!statusCounts[project.estado]) {
      statusCounts[project.estado] = { count: 0, color: project.cor_estado };
    }
    statusCounts[project.estado].count++;
  }

  const labels = Object.keys(statusCounts);
  const data = labels.map(label => statusCounts[label].count);
  const backgroundColors = labels.map(label => statusCounts[label].color);

  return {
    labels,
    datasets: [
      {
        label: 'Projetos por Status',
        data,
        backgroundColor: backgroundColors,
        borderColor: '#1e293b', // slate-800 for separation
        borderWidth: 2,
      },
    ],
  };
});

const chartOptions = computed<ChartOptions<'doughnut'>>(() => ({
  responsive: true,
  aspectRatio: 1,
  cutout: '60%', // Gráfico um pouco mais grosso para caber os labels
  plugins: {
    legend: {
      display: false,
    },
    datalabels: {
      display: true,
      color: '#fff',
      font: {
        family: 'monospace',
        weight: 'bold',
        size: 12,
      },
      formatter: (value) => {
        return value > 0 ? value : '';
      },
    },
    tooltip: {
      bodyFont: {
          family: 'monospace'
      },
      titleFont: {
          family: 'monospace'
      }
    }
  },
}));
</script>
