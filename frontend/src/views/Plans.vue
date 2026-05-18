<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold">DCA Plans</h1>
      <button @click="openCreate" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
        + New Plan
      </button>
    </div>

    <div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-gray-400 border-b border-gray-800 bg-gray-800/50">
            <th class="text-left px-4 py-3">Name</th>
            <th class="text-left px-4 py-3">Exchange</th>
            <th class="text-left px-4 py-3">Pair</th>
            <th class="text-right px-4 py-3">Amount</th>
            <th class="text-left px-4 py-3">Schedule</th>
            <th class="text-left px-4 py-3">Status</th>
            <th class="text-left px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!plans.length">
            <td colspan="7" class="text-center text-gray-500 py-12">No plans yet. Create your first DCA plan.</td>
          </tr>
          <tr v-for="p in plans" :key="p.id" class="border-b border-gray-800/50 hover:bg-gray-800/30">
            <td class="px-4 py-3 font-medium">{{ p.name }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <img :src="exchangeLogo(p.exchange)" :alt="p.exchange" class="w-5 h-5 rounded-full object-cover" />
                <span class="capitalize">{{ p.exchange }}</span>
              </div>
            </td>
            <td class="px-4 py-3 font-mono">{{ p.symbol }}</td>
            <td class="px-4 py-3 text-right">{{ p.quote_amount }} {{ p.currency }}</td>
            <td class="px-4 py-3 text-gray-400 text-xs">{{ cronLabel(p.schedule_cron) }}</td>
            <td class="px-4 py-3">
              <span :class="statusClass(p.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">{{ p.status }}</span>
            </td>
            <td class="px-4 py-3">
              <div class="flex gap-2 flex-wrap">
                <button v-if="p.status === 'active'" @click="pausePlan(p.id)" class="text-yellow-400 hover:text-yellow-300 text-xs px-2 py-1 border border-yellow-800 rounded transition-colors">Pause</button>
                <button v-if="p.status === 'paused'" @click="resumePlan(p.id)" class="text-green-400 hover:text-green-300 text-xs px-2 py-1 border border-green-800 rounded transition-colors">Resume</button>
                <button v-if="p.status === 'active'" @click="triggerNow(p.id)" class="text-indigo-400 hover:text-indigo-300 text-xs px-2 py-1 border border-indigo-800 rounded transition-colors">Buy Now</button>
                <button @click="openEdit(p)" class="text-blue-400 hover:text-blue-300 text-xs px-2 py-1 border border-blue-800 rounded transition-colors">Edit</button>
                <button @click="openSell(p)" class="text-red-400 hover:text-red-300 text-xs px-2 py-1 border border-red-800 rounded transition-colors">Sell</button>
                <button @click="copyInfo(p)" class="text-gray-400 hover:text-gray-200 text-xs px-2 py-1 border border-gray-700 rounded transition-colors">{{ copied === p.id ? '✓' : '⎘' }}</button>
                <button @click="confirmDelete(p)" class="text-red-400 hover:text-red-300 text-xs px-2 py-1 border border-red-900 rounded transition-colors">Delete</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Plan Modal -->
    <div v-if="showCreate" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 overflow-y-auto" @click.self="showCreate = false">
      <div class="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl my-4">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 class="text-base font-semibold">New DCA Plan</h2>
          <button @click="showCreate = false" class="text-gray-500 hover:text-gray-300 text-xl leading-none">&times;</button>
        </div>
        <form @submit.prevent="createPlan" class="px-6 py-5 flex flex-col gap-5">

          <!-- Exchange -->
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Exchange</p>
            <div class="grid grid-cols-2 gap-3">
              <button type="button" v-for="ex in exchanges" :key="ex.id"
                @click="form.exchange = ex.id"
                :class="form.exchange === ex.id ? 'border-indigo-500 bg-indigo-500/10 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'"
                class="border rounded-xl py-3 text-sm font-medium transition-all flex flex-col items-center gap-2">
                <img :src="ex.logo" :alt="ex.id" class="w-8 h-8 rounded-full object-cover" />
                <span class="capitalize">{{ ex.id }}</span>
                <span class="text-xs opacity-60">{{ ex.pairs }}</span>
              </button>
            </div>
          </div>

          <!-- Symbol -->
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Trading Pair</p>
            <input v-model="symbolSearch" type="text" placeholder="Search e.g. BTC, ETH..."
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500 mb-2" />
            <div class="max-h-40 overflow-y-auto rounded-lg border border-gray-700 bg-gray-800">
              <div v-if="symbolsLoading" class="text-center text-gray-500 text-sm py-4">Loading...</div>
              <div v-else-if="!filteredSymbols.length" class="text-center text-gray-500 text-sm py-4">No results</div>
              <button v-for="s in filteredSymbols" :key="s" type="button"
                @click="form.symbol = s; symbolSearch = s"
                :class="form.symbol === s ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'"
                class="w-full text-left px-3 py-2 text-sm transition-colors font-mono">{{ s }}</button>
            </div>
            <p v-if="form.symbol" class="text-xs text-indigo-400 mt-1">Selected: <b>{{ form.symbol }}</b></p>
          </div>

          <!-- Amount -->
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Amount per order</p>
            <div class="flex gap-2 flex-wrap mb-2">
              <button v-for="preset in amountPresets" :key="preset" type="button"
                @click="form.quote_amount = preset"
                :class="form.quote_amount === preset ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-gray-500'"
                class="border rounded-lg px-3 py-1.5 text-sm transition-colors">{{ preset }} {{ form.currency }}</button>
            </div>
            <div class="flex gap-2 items-center">
              <input v-model.number="form.quote_amount" type="number" :min="minAmount(form.exchange)" step="any"
                class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500" />
              <span class="text-gray-400 text-sm font-medium w-12 text-center">{{ form.currency }}</span>
            </div>
            <p v-if="form.quote_amount < minAmount(form.exchange)" class="text-red-400 text-xs mt-1">
              ขั้นต่ำ {{ minAmount(form.exchange) }} {{ form.currency }}
            </p>
          </div>

          <!-- Schedule — alarm clock UX -->
          <SchedulePicker v-model="form.schedule_cron" />

          <!-- Plan name -->
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Plan Name</p>
            <input v-model="form.name" type="text" :placeholder="namePlaceholder" required
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500" />
          </div>

          <div class="flex gap-3 pt-1">
            <button type="button" @click="showCreate = false" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2.5 rounded-xl text-sm transition-colors">Cancel</button>
            <button type="submit" :disabled="!form.symbol || !form.name || form.quote_amount < minAmount(form.exchange)"
              class="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white py-2.5 rounded-xl text-sm font-medium transition-colors">
              Create Plan
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Plan Modal -->
    <div v-if="showEdit" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 overflow-y-auto" @click.self="showEdit = false">
      <div class="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl my-4">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 class="text-base font-semibold">Edit Plan</h2>
          <button @click="showEdit = false" class="text-gray-500 hover:text-gray-300 text-xl leading-none">&times;</button>
        </div>
        <form @submit.prevent="savePlan" class="px-6 py-5 flex flex-col gap-5">
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Exchange</p>
            <div class="flex items-center gap-3 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3">
              <img :src="exchangeLogo(editForm.exchange)" class="w-7 h-7 rounded-full object-cover" />
              <span class="capitalize text-white">{{ editForm.exchange }}</span>
              <span class="text-gray-600 text-xs ml-1">(ไม่สามารถเปลี่ยนได้)</span>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Trading Pair</p>
            <div class="bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 font-mono text-indigo-300">
              {{ editForm.symbol }} <span class="text-gray-600 text-xs ml-2">(ไม่สามารถเปลี่ยนได้)</span>
            </div>
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Amount per order</p>
            <div class="flex gap-2 flex-wrap mb-2">
              <button v-for="preset in editAmountPresets" :key="preset" type="button"
                @click="editForm.quote_amount = preset"
                :class="editForm.quote_amount === preset ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-gray-500'"
                class="border rounded-lg px-3 py-1.5 text-sm transition-colors">{{ preset }} {{ editForm.currency }}</button>
            </div>
            <div class="flex gap-2 items-center">
              <input v-model.number="editForm.quote_amount" type="number" :min="minAmount(editForm.exchange)" step="any"
                class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500" />
              <span class="text-gray-400 text-sm font-medium w-12 text-center">{{ editForm.currency }}</span>
            </div>
            <p v-if="editForm.quote_amount < minAmount(editForm.exchange)" class="text-red-400 text-xs mt-1">
              ขั้นต่ำ {{ minAmount(editForm.exchange) }} {{ editForm.currency }}
            </p>
          </div>
          <SchedulePicker v-model="editForm.schedule_cron" />
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Plan Name</p>
            <input v-model="editForm.name" type="text" required
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500" />
          </div>
          <div>
            <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Max Retries</p>
            <input v-model.number="editForm.max_retries" type="number" min="0" max="10"
              class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500" />
          </div>
          <div class="flex gap-3 pt-1">
            <button type="button" @click="showEdit = false" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2.5 rounded-xl text-sm transition-colors">Cancel</button>
            <button type="submit" :disabled="!editForm.name || editForm.quote_amount < minAmount(editForm.exchange)"
              class="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white py-2.5 rounded-xl text-sm font-medium transition-colors">
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="deleteTarget" class="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div class="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-sm text-center shadow-2xl">
        <div class="text-3xl mb-3">🗑️</div>
        <p class="text-base font-semibold mb-1">Delete "{{ deleteTarget.name }}"?</p>
        <p class="text-gray-400 text-sm mb-6">แผนนี้จะถูกลบและหยุดทำงานทันที</p>
        <div class="flex gap-3">
          <button @click="deleteTarget = null" class="flex-1 bg-gray-800 hover:bg-gray-700 py-2.5 rounded-xl text-sm transition-colors">Cancel</button>
          <button @click="deletePlan()" class="flex-1 bg-red-600 hover:bg-red-700 text-white py-2.5 rounded-xl text-sm font-medium transition-colors">Delete</button>
        </div>
      </div>
    </div>

    <!-- Sell Modal -->
    <SellModal v-if="sellTarget" :plan="sellTarget" @close="sellTarget = null" @done="sellDone()" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { plansApi } from '../api'
import SchedulePicker from '../components/SchedulePicker.vue'
import SellModal from '../components/SellModal.vue'

const plans = ref<any[]>([])
const showCreate = ref(false)
const showEdit = ref(false)
const deleteTarget = ref<any>(null)
const copied = ref<string | null>(null)
const editTarget = ref<any>(null)
const sellTarget = ref<any>(null)

function openSell(p: any) { sellTarget.value = p }
async function sellDone() { sellTarget.value = null }

const MIN_AMOUNT: Record<string, number> = { bitkub: 10, binance: 5 }
function minAmount(exchange: string): number { return MIN_AMOUNT[exchange] ?? 1 }

const defaultEditForm = () => ({ name: '', exchange: '', symbol: '', quote_amount: 0, currency: '', schedule_cron: '0 9 * * *', max_retries: 3 })
const editForm = ref(defaultEditForm())
const editAmountPresets = computed(() => editForm.value.exchange === 'bitkub' ? [500, 1000, 2000, 5000] : [10, 50, 100, 500])

function openEdit(p: any) {
  editTarget.value = p
  editForm.value = { name: p.name, exchange: p.exchange, symbol: p.symbol, quote_amount: parseFloat(p.quote_amount), currency: p.currency, schedule_cron: p.schedule_cron, max_retries: p.max_retries ?? 3 }
  showEdit.value = true
}

async function savePlan() {
  await plansApi.update(editTarget.value.id, { name: editForm.value.name, quote_amount: editForm.value.quote_amount, schedule_cron: editForm.value.schedule_cron, max_retries: editForm.value.max_retries })
  showEdit.value = false
  await load()
}

function copyInfo(p: any) {
  navigator.clipboard.writeText(`Plan: ${p.name}\nExchange: ${p.exchange}\nSymbol: ${p.symbol}\nAmount: ${p.quote_amount} ${p.currency}\nSchedule: ${p.schedule_cron}\nStatus: ${p.status}\nID: ${p.id}`)
  copied.value = p.id
  setTimeout(() => { copied.value = null }, 2000)
}

const symbols = ref<string[]>([])
const symbolsLoading = ref(false)
const symbolSearch = ref('')
const defaultForm = () => ({ name: '', exchange: 'binance', symbol: '', quote_amount: 100, currency: 'USDT', schedule_cron: '0 9 * * *', max_retries: 3 })
const form = ref(defaultForm())

const exchanges = [
  { id: 'binance', logo: '/binance.jpg', pairs: 'USDT pairs' },
  { id: 'bitkub', logo: '/bitkub.png', pairs: 'THB pairs' },
]
function exchangeLogo(ex: string) { return exchanges.find(e => e.id === ex)?.logo ?? '' }
const amountPresets = computed(() => form.value.exchange === 'bitkub' ? [500, 1000, 2000, 5000] : [10, 50, 100, 500])
const filteredSymbols = computed(() => symbolSearch.value ? symbols.value.filter(s => s.toLowerCase().includes(symbolSearch.value.toLowerCase())) : symbols.value)
const namePlaceholder = computed(() => form.value.symbol ? `${form.value.symbol} DCA` : 'e.g. BTC Daily')

async function loadSymbols(exchange: string) {
  symbolsLoading.value = true; symbols.value = []; form.value.symbol = ''; symbolSearch.value = ''
  try { const res = await plansApi.symbols(exchange); symbols.value = res.data } finally { symbolsLoading.value = false }
}

watch(() => form.value.exchange, (ex) => {
  form.value.currency = ex === 'bitkub' ? 'THB' : 'USDT'
  form.value.quote_amount = ex === 'bitkub' ? 1000 : 100
  loadSymbols(ex)
})

async function load() { const res = await plansApi.list(); plans.value = res.data }

function openCreate() {
  form.value = defaultForm(); symbolSearch.value = ''; showCreate.value = true; loadSymbols(form.value.exchange)
}

async function createPlan() {
  const payload = { ...form.value }
  if (!payload.name) payload.name = namePlaceholder.value
  await plansApi.create(payload)
  showCreate.value = false; await load()
}

async function pausePlan(id: string) { await plansApi.pause(id); await load() }
async function resumePlan(id: string) { await plansApi.resume(id); await load() }
async function triggerNow(id: string) { await plansApi.trigger(id) }
function confirmDelete(p: any) { deleteTarget.value = p }
async function deletePlan() { await plansApi.delete(deleteTarget.value.id); deleteTarget.value = null; await load() }

function statusClass(s: string) {
  return { active: 'bg-green-900 text-green-300', paused: 'bg-yellow-900 text-yellow-300', deleted: 'bg-gray-700 text-gray-400' }[s] ?? ''
}

function cronLabel(cron: string): string {
  const map: Record<string, string> = {
    '0 9 * * *': 'ทุกวัน 09:00',
    '0 9 * * 1': 'ทุกวันจันทร์ 09:00',
    '0 9 1 * *': 'ทุกวันที่ 1 09:00',
    '0 */4 * * *': 'ทุก 4 ชั่วโมง',
  }
  return map[cron] ?? cron
}

onMounted(load)
</script>
