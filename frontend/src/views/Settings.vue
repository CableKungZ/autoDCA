<template>
  <div class="max-w-2xl">
    <h1 class="text-2xl font-bold mb-8">Settings</h1>

    <div class="flex flex-col gap-4">
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-sm text-gray-300 flex flex-col gap-3">
        <p class="text-gray-400">Configure via <code class="text-indigo-300">.env</code> at the project root, then restart:</p>
        <code class="block bg-gray-800 rounded px-3 py-2 text-indigo-300">docker compose restart api scheduler</code>
      </div>

      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-sm flex flex-col gap-2">
        <p class="text-gray-400 font-medium mb-1">Required environment variables</p>
        <div v-for="v in vars" :key="v.key" class="flex gap-3">
          <code class="text-indigo-300 w-52 shrink-0">{{ v.key }}</code>
          <span class="text-gray-500">{{ v.desc }}</span>
        </div>
      </div>

      <!-- Server IP -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-6 text-sm flex flex-col gap-2">
        <p class="text-gray-400 font-medium mb-1">Server Public IP (whitelist in Exchange)</p>
        <div class="flex items-center gap-3">
          <code class="text-green-300 text-base font-mono">{{ serverIp || 'Loading...' }}</code>
          <button v-if="serverIp" @click="copyIp" class="text-xs text-gray-500 hover:text-gray-300 border border-gray-700 px-2 py-0.5 rounded">
            {{ copied ? 'Copied!' : 'Copy' }}
          </button>
        </div>
        <p class="text-gray-600 text-xs">Add this IP to your Binance / Bitkub API Key whitelist</p>
      </div>

      <p class="text-yellow-400 text-sm bg-yellow-950 border border-yellow-900 rounded-lg px-4 py-3">
        Use <b>read + trade only</b> permission — do not enable withdrawal permission
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const serverIp = ref('')
const copied = ref(false)

onMounted(async () => {
  try {
    const res = await fetch('/api/system/ip')
    const data = await res.json()
    serverIp.value = data.ip
  } catch {}
})

function copyIp() {
  navigator.clipboard.writeText(serverIp.value)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

const vars = [
  { key: 'BINANCE_API_KEY', desc: 'Binance API Key' },
  { key: 'BINANCE_API_SECRET', desc: 'Binance API Secret' },
  { key: 'BITKUB_API_KEY', desc: 'Bitkub API Key' },
  { key: 'BITKUB_API_SECRET', desc: 'Bitkub API Secret' },
  { key: 'TELEGRAM_BOT_TOKEN', desc: 'Telegram Bot Token from @BotFather' },
  { key: 'TELEGRAM_CHAT_ID', desc: 'Chat ID of the notification recipient' },
  { key: 'FERNET_KEY', desc: 'Key for encrypting API keys in DB' },
]
</script>
