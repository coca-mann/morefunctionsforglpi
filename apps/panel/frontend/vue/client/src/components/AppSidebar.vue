<template>
  <div class="w-20 bg-slate-900 border-r border-slate-700 flex flex-col items-center py-4 gap-2 fixed left-0 top-16 h-[calc(100vh-64px)]">
    <!-- Logo/Home -->
    <div class="w-14 h-14 bg-gradient-to-br from-blue-600 to-blue-800 rounded flex items-center justify-center mb-4 cursor-pointer hover:from-blue-500 hover:to-blue-700 transition-all" title="Home">
      <span class="text-white text-2xl font-bold">TI</span>
    </div>

    <!-- Menu Items -->
    <div class="flex-1 flex flex-col gap-2">
      <button
        v-for="item in menuItems"
        :key="item.id"
        @click="selectMenu(item.id)"
        class="relative w-14 h-14 rounded flex items-center justify-center transition-all group"
        :class="[
          activeMenuId === item.id
            ? 'bg-slate-700 border-l-4 border-blue-500'
            : 'hover:bg-slate-800'
        ]"
        :title="item.label"
      >
        <!-- Ícone -->
        <span class="material-icons text-xl" :class="activeMenuId === item.id ? 'text-blue-400' : 'text-slate-400'">
          {{ item.icon }}
        </span>

        <!-- Tooltip -->
        <div class="absolute left-full ml-2 px-3 py-2 bg-slate-800 text-slate-100 text-sm rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          {{ item.label }}
        </div>

        <!-- Indicador de notificação -->
        <div
          v-if="item.notificationCount && item.notificationCount > 0"
          class="absolute top-1 right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center text-xs font-bold text-white"
        >
          {{ item.notificationCount > 9 ? '9+' : item.notificationCount }}
        </div>
      </button>
    </div>

    <!-- Separador -->
    <div class="w-12 h-px bg-slate-700 my-2"></div>

    <!-- Controles Inferiores -->
    <div class="flex flex-col gap-2">
      <!-- Status de Conexão -->
      <button
        class="w-14 h-14 rounded flex items-center justify-center transition-all group"
        :class="wsConnected ? 'bg-green-900 hover:bg-green-800' : 'bg-red-900 hover:bg-red-800'"
        :title="wsConnected ? 'Conectado' : 'Desconectado'"
      >
        <span class="material-icons text-xl" :class="wsConnected ? 'text-green-400' : 'text-red-400'">
          {{ wsConnected ? 'cloud_done' : 'cloud_off' }}
        </span>

        <!-- Tooltip -->
        <div class="absolute left-full ml-2 px-3 py-2 bg-slate-800 text-slate-100 text-sm rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          {{ wsConnected ? 'Conectado' : 'Desconectado' }}
        </div>
      </button>

      <!-- Som -->
      <button
        @click="toggleSound"
        class="w-14 h-14 rounded flex items-center justify-center transition-all group"
        :class="soundEnabledLocal ? 'bg-slate-700 hover:bg-slate-600' : 'bg-slate-800 hover:bg-slate-700'"
        :title="soundEnabledLocal ? 'Som ativado' : 'Som desativado'"
      >
        <span class="material-icons text-xl" :class="soundEnabledLocal ? 'text-yellow-400' : 'text-slate-500'">
          {{ soundEnabledLocal ? 'volume_up' : 'volume_off' }}
        </span>

        <!-- Tooltip -->
        <div class="absolute left-full ml-2 px-3 py-2 bg-slate-800 text-slate-100 text-sm rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          {{ soundEnabledLocal ? 'Som ativado' : 'Som desativado' }}
        </div>
      </button>

      <!-- Teste (apenas em desenvolvimento) -->
      <button
        v-if="isDevelopment"
        @click="toggleTestPanel"
        class="w-14 h-14 rounded flex items-center justify-center transition-all group bg-purple-900 hover:bg-purple-800"
        title="Painel de Teste"
      >
        <span class="material-icons text-xl text-purple-400">
          bug_report
        </span>

        <!-- Tooltip -->
        <div class="absolute left-full ml-2 px-3 py-2 bg-slate-800 text-slate-100 text-sm rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
          Painel de Teste
        </div>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface MenuItem {
  id: string
  label: string
  icon: string
  notificationCount?: number
}

const emit = defineEmits<{
  'select-menu': [id: string]
  'toggle-sound': []
  'toggle-test-panel': []
}>()

const props = defineProps<{
  activeMenu?: string
  wsConnected?: boolean
  soundEnabled?: boolean
}>()

const soundEnabledLocal = ref(props.soundEnabled ?? false)
const isDevelopment = import.meta.env.DEV

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: 'dashboard'
  },
  {
    id: 'tickets',
    label: 'Tickets',
    icon: 'assignment'
  },
  {
    id: 'projects',
    label: 'Projetos',
    icon: 'folder_open'
  },
  {
    id: 'remote',
    label: 'Administração',
    icon: 'settings'
  }
]

const activeMenuId = computed(() => props.activeMenu || 'dashboard')
const wsConnected = computed(() => props.wsConnected ?? false)

const selectMenu = (id: string) => {
  emit('select-menu', id)
}

const toggleSound = () => {
  soundEnabledLocal.value = !soundEnabledLocal.value
  emit('toggle-sound')
}

const toggleTestPanel = () => {
  emit('toggle-test-panel')
}
</script>

<style scoped>
/* Estilos customizados para sidebar */
.material-icons {
  user-select: none;
  font-feature-settings: 'liga';
}

/* Animação suave para tooltips */
@keyframes tooltip-fade {
  from {
    opacity: 0;
    transform: translateX(-4px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.group:hover > div {
  animation: tooltip-fade 0.2s ease-out;
}
</style>
