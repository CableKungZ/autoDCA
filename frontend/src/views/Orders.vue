<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Order History</h1>
      <button
        @click="showThb = !showThb"
        :class="['px-3 py-1 rounded-lg text-sm border transition-colors', showThb ? 'bg-amber-600 border-amber-500 text-white' : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white']"
      >฿ THB</button>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3 mb-6">
      <select v-model="filters.exchange" @change="load" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200">
        <option value="">All Exchanges</option>
        <option value="binance">Binance</option>
        <option value="bitkub">Bitkub</option>
      </select>
      <input v-model="filters.symbol" @change="load" placeholder="Symbol (e.g. BTC/USDT)" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200 w-44" />
      <select v-model="filters.status" @change="load" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200">
        <option value="">All Status</option>
        <option value="filled">Filled</option>
        <option value="pending">Pending</option>
        <option value="failed">Failed</option>
      </select>
      <input v-model="filters.date_from" type="date" @change="load" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200" />
      <input v-model="filters.date_to" type="date" @change="load" class="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200" />
    </div>

    <div class="flex justify-end mb-3">
      <button @click="clearPending" class="px-4 py-1.5 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg">
        Clear Pending
      </button>
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <OrderTable :orders="orders" :showThb="showThb" />
    </div>

    <!-- Pagination -->
    <div class="flex justify-between items-center mt-4 text-sm text-gray-400">
      <span>Showing {{ orders.length }} orders</span>
      <div class="flex gap-2">
        <button @click="prevPage" :disabled="offset === 0" class="px-3 py-1 bg-gray-800 rounded disabled:opacity-40">Prev</button>
        <button @click="nextPage" :disabled="orders.length < limit" class="px-3 py-1 bg-gray-800 rounded disabled:opacity-40">Next</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ordersApi } from '../api'
import OrderTable from '../components/OrderTable.vue'

const orders = ref<any[]>([])
const showThb = ref(true)
const limit = 50
const offset = ref(0)
const filters = ref({ exchange: '', symbol: '', status: '', date_from: '', date_to: '' })

async function load() {
  const params: any = { limit, offset: offset.value, ...Object.fromEntries(Object.entries(filters.value).filter(([, v]) => v)) }
  const res = await ordersApi.list(params)
  orders.value = res.data
}

async function clearPending() {
  if (!confirm('Cancel all pending orders?')) return
  const res = await ordersApi.clearPending()
  alert(`Cleared ${res.data.cleared} pending order(s)`)
  load()
}

function prevPage() { if (offset.value >= limit) { offset.value -= limit; load() } }
function nextPage() { offset.value += limit; load() }

onMounted(load)
</script>
