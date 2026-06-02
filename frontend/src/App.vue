<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <nav class="w-56 bg-gray-900 border-r border-gray-800 flex flex-col py-6 px-4 gap-1 fixed h-full">
      <div class="text-xl font-bold text-indigo-400 mb-8 px-2">⚡ AutoDCA</div>
      <RouterLink
        v-for="item in nav"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        active-class="bg-indigo-600 text-white"
      >
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </RouterLink>

      <!-- WS status -->
      <div class="mt-auto flex items-center gap-2 px-2 py-1">
        <span :class="wsConnected ? 'bg-green-400 animate-pulse' : 'bg-red-500'" class="w-2 h-2 rounded-full"></span>
        <span class="text-xs text-gray-500">{{ wsConnected ? 'Live' : 'Offline' }}</span>
      </div>
    </nav>

    <!-- Main content -->
    <main class="flex-1 ml-56 p-8">
      <!-- Toast notification -->
      <transition name="toast">
        <div v-if="toast" class="fixed top-5 right-5 z-[100] bg-gray-800 border border-gray-700 rounded-xl px-5 py-3 shadow-2xl flex items-center gap-3 text-sm">
          <span>{{ toast.icon }}</span>
          <div>
            <p class="font-medium text-white">{{ toast.title }}</p>
            <p class="text-gray-400 text-xs">{{ toast.body }}</p>
          </div>
        </div>
      </transition>
      <RouterView :key="reloadKey" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useStatsStore } from './stores/stats'

const nav = [
  { path: '/', icon: '📊', label: 'Dashboard' },
  { path: '/plans', icon: '📋', label: 'DCA Plans' },
  { path: '/orders', icon: '📦', label: 'Orders' },
  { path: '/settings', icon: '⚙️', label: 'Settings' },
]

const statsStore = useStatsStore()
const wsConnected = ref(false)
const reloadKey = ref(0)
const toast = ref<{ icon: string; title: string; body: string } | null>(null)
let toastTimer: ReturnType<typeof setTimeout> | null = null
let socket: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null

function showToast(icon: string, title: string, body: string) {
  toast.value = { icon, title, body }
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = null }, 4000)
}

function triggerReload() {
  reloadKey.value++
}

function getWsUrl() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${location.host}/ws`
}

function connect() {
  socket = new WebSocket(getWsUrl())

  socket.onopen = () => { wsConnected.value = true }

  socket.onmessage = (e) => {
    try {
      const { event, data } = JSON.parse(e.data)
      if (event === 'order_filled') {
        showToast('✅', 'Order Filled', `${data.symbol} ${data.side ?? 'buy'}`)
        statsStore.invalidate()
        triggerReload()
      } else if (event === 'order_failed') {
        showToast('⚠️', 'Order Failed', data.symbol)
        statsStore.invalidate()
        triggerReload()
      }
    } catch {}
  }

  socket.onclose = () => {
    wsConnected.value = false
    reconnectTimer = setTimeout(connect, 3000)
  }

  socket.onerror = () => { socket?.close() }

  const ping = setInterval(() => {
    if (socket?.readyState === WebSocket.OPEN) socket.send('ping')
    else clearInterval(ping)
  }, 30_000)
}

onMounted(connect)
onUnmounted(() => {
  socket?.close()
  if (reconnectTimer) clearTimeout(reconnectTimer)
})
</script>

<style scoped>
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translateX(20px); }
</style>
