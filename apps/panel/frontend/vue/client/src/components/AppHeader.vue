<template>
  <header
    class="fixed top-0 left-0 right-0 h-16 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-6 z-50">
    <!-- Esquerda: Status, ID e IP -->
    <div class="flex items-center gap-4">
      <!-- Indicador WebSocket com 3 estados -->
      <div class="flex items-center gap-2">
        <div :class="[
          'w-3 h-3 rounded-full transition-all',
          connectionStatus === 'connected' ? 'bg-green-500 animate-pulse' :
            connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
              connectionStatus === 'reconnecting' ? 'bg-orange-500 animate-pulse' :
                'bg-red-500'
        ]" :title="statusLabel" />
        <span :class="[
          'text-sm font-mono',
          connectionStatus === 'connected' ? 'text-green-400' :
            connectionStatus === 'connecting' ? 'text-yellow-400' :
              connectionStatus === 'reconnecting' ? 'text-orange-400' :
                'text-red-400'
        ]">
          {{ statusLabel }}
        </span>
      </div>

      <!-- ID Único e IP -->
      <div class="pl-4 border-l border-slate-700 space-y-1">
        <div class="text-sm font-bold font-mono text-slate-100">{{ clientId }}</div>
        <div class="text-xs font-mono text-slate-400">{{ clientIp }}</div>
      </div>
    </div>

    <!-- Centro: Título -->
    <div class="text-center">
      <h1 class="text-lg font-bold text-slate-100 font-mono">PAINEL OPERACIONAL DE TI</h1>
    </div>

    <!-- Direita: Relógio Digital -->
    <div class="text-right">
      <div class="text-3xl font-bold font-mono text-green-400 tracking-wider">
        {{ currentTime }}
      </div>
      <div class="text-xs text-slate-400 font-mono mt-1">{{ timezone }}</div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  clientId: string
  clientIp: string
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'reconnecting' | 'error'
  currentTime: string
  timezone: string
}

const props = defineProps<Props>()

const statusLabel = computed(() => {
  switch (props.connectionStatus) {
    case 'connected':
      return 'Online'
    case 'connecting':
      return 'Conectando...'
    case 'reconnecting':
      return 'Reconectando...'
    case 'disconnected':
      return 'Offline'
    case 'error':
      return 'Erro de Conexão'
    default:
      return 'Desconhecido'
  }
})
</script>

<style scoped>
/* Estilos específicos do header */
</style>
