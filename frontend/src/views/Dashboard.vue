<template>
  <div>
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold">Dashboard</h1>
      <div class="flex items-center gap-2">
        <!-- THB toggle -->
        <button
          @click="showThb = !showThb"
          :class="['px-3 py-1 rounded-lg text-sm border transition-colors', showThb ? 'bg-amber-600 border-amber-500 text-white' : 'bg-gray-800 border-gray-700 text-gray-400 hover:text-white']"
        >฿ THB</button>
        <!-- Plan selector -->
        <button
          @click="selectedPlanId = null"
          :class="['px-3 py-1 rounded-lg text-sm transition-colors', !selectedPlanId ? 'bg-indigo-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white']"
        >All Plans</button>
        <select
          v-model="selectedPlanId"
          class="bg-gray-800 border border-gray-700 text-gray-200 rounded-lg px-3 py-1 text-sm"
        >
          <option :value="null">— Select Plan —</option>
          <option v-for="p in plans" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </div>

    <!-- Stat cards -->
    <div class="grid grid-cols-2 xl:grid-cols-4 gap-4 mb-8">
      <StatCard title="Total Invested" :value="fmt(totalInvestedDisplay)" :sub="summarySubLabel" color="indigo" />
      <StatCard v-if="selectedPlanId" title="Avg DCA Price" :value="fmtAvgCost" :sub="avgCostSub" color="blue" />
      <StatCard title="Unrealized PnL" :value="fmtPnl(totalPnlDisplay)" :sub="pnlPct" :positive="totalPnlThb >= 0" color="green" />
      <StatCard title="Active Plans" :value="String(activePlans)" sub="plans" color="purple" />
    </div>

    <!-- Per-plan breakdown -->
    <div v-if="visibleStats.length" class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
      <div v-for="s in visibleStats" :key="s.plan_id" class="bg-gray-900 border border-gray-800 rounded-xl p-4 text-sm">
        <div class="flex justify-between items-start mb-3">
          <div>
            <span class="font-semibold text-white">{{ s.name }}</span>
            <span class="ml-2 text-gray-500 text-xs">{{ s.exchange.toUpperCase() }} · {{ s.symbol }}</span>
          </div>
          <div class="flex items-center gap-2">
            <span :class="s.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'" class="text-xs font-mono">
              {{ s.unrealized_pnl >= 0 ? '+' : '' }}{{ fmt(displayVal(s.unrealized_pnl, s.unrealized_pnl_thb, s.currency, s.thb_rate)) }} {{ displayCur(s.currency) }}
              ({{ planPnlPct(s) }}%)
            </span>
            <button @click="copyPlanJson(s)" class="text-gray-600 hover:text-gray-300 text-xs border border-gray-700 px-1.5 py-0.5 rounded" title="Copy JSON">
              {{ copiedId === s.plan_id ? '✓' : '{}' }}
            </button>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2 mb-2">
          <div>
            <p class="text-gray-600 text-xs mb-0.5">Invested</p>
            <p class="text-white font-mono">{{ fmt(displayVal(s.total_invested, s.total_invested_thb, s.currency, s.thb_rate)) }}</p>
            <p class="text-gray-600 text-xs">{{ displayCur(s.currency) }}</p>
          </div>
          <div>
            <p class="text-gray-600 text-xs mb-0.5">Avg Cost</p>
            <p class="text-white font-mono">{{ fmt(displayVal(s.avg_cost, s.avg_cost_thb, s.currency, s.thb_rate)) }}</p>
            <p class="text-gray-600 text-xs">{{ displayCur(s.currency) }}</p>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <p class="text-gray-600 text-xs mb-0.5">Current Price</p>
            <p class="text-yellow-300 font-mono">{{ fmt(displayVal(s.current_price, s.current_price_thb, s.currency, s.thb_rate)) }}</p>
            <p class="text-gray-600 text-xs">{{ displayCur(s.currency) }}</p>
          </div>
          <div>
            <p class="text-gray-600 text-xs mb-0.5">Holdings</p>
            <p class="text-white font-mono">{{ s.total_coins.toFixed(8) }}</p>
            <p class="text-gray-600 text-xs">{{ s.symbol.split('/')[0] }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- THB/USDT Rate Chart -->
    <div class="bg-gray-900 rounded-xl border border-gray-800 p-6 mb-8">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="font-semibold text-gray-200">THB / USDT Rate</h2>
          <p v-if="currentRate" class="text-amber-400 text-sm mt-0.5">Current: {{ currentRate.toFixed(2) }} THB</p>
        </div>
        <select v-model="rateDays" class="bg-gray-800 border border-gray-700 text-gray-200 rounded px-2 py-1 text-sm">
          <option :value="7">7 days</option>
          <option :value="30">30 days</option>
          <option :value="90">90 days</option>
        </select>
      </div>
      <apexchart v-if="rateSeries.length" type="line" height="200" :options="rateChartOptions" :series="rateSeries" />
      <div v-else class="text-gray-500 text-sm text-center py-8">No rate data yet</div>
    </div>

    <!-- Recent orders -->
    <div class="bg-gray-900 rounded-xl border border-gray-800 p-6">
      <h2 class="font-semibold text-gray-200 mb-4">Recent Orders</h2>
      <OrderTable :orders="recentOrders" :compact="true" :showThb="showThb" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ratesApi, ordersApi, plansApi } from '../api'
import { useStatsStore } from '../stores/stats'
import StatCard from '../components/StatCard.vue'
import OrderTable from '../components/OrderTable.vue'

const statsStore = useStatsStore()
const plans = ref<any[]>([])
const selectedPlanId = ref<string | null>(null)
const stats = ref<any[]>([])
const rateData = ref<any[]>([])
const recentOrders = ref<any[]>([])
const rateDays = ref(30)
const showThb = ref(true)

const currentRate = computed(() => {
  if (!rateData.value.length) return null
  return parseFloat(rateData.value[rateData.value.length - 1].rate)
})

// Convert any amount to THB using latest rate
function toThb(amount: number, currency: string): number {
  if (currency === 'THB') return amount
  const rate = currentRate.value || 1
  return amount * rate
}

const visibleStats = computed(() =>
  selectedPlanId.value ? stats.value.filter(s => s.plan_id === selectedPlanId.value) : stats.value
)

// Convert to THB — prefer backend-computed thb value, fallback to live rate
function toThbVal(nativeVal: number, thbVal: number, currency: string): number {
  if (currency === 'THB') return nativeVal
  if (thbVal && thbVal > 0) return thbVal
  return nativeVal * (currentRate.value || 1)
}

// Always show in THB for PnL percentage base
const totalInvestedThb = computed(() =>
  visibleStats.value.reduce((sum, s) => sum + toThbVal(s.total_invested, s.total_invested_thb, s.currency), 0)
)
const totalPnlThb = computed(() =>
  visibleStats.value.reduce((sum, s) => sum + toThbVal(s.unrealized_pnl, s.unrealized_pnl_thb, s.currency), 0)
)

// Display values — toggle between USDT and THB
const totalInvestedDisplay = computed(() => {
  if (showThb.value) return totalInvestedThb.value
  return visibleStats.value.reduce((sum, s) => sum + toUsdtVal(s.total_invested, s.currency, s.thb_rate), 0)
})
const totalPnlDisplay = computed(() => {
  if (showThb.value) return totalPnlThb.value
  return visibleStats.value.reduce((sum, s) => sum + toUsdtVal(s.unrealized_pnl, s.currency, s.thb_rate), 0)
})
const summarySubLabel = computed(() => showThb.value ? 'THB' : 'USDT')
const totalInvestedForPct = computed(() => totalInvestedThb.value)

const isSingleCurrency = computed(() => {
  const cur = [...new Set(visibleStats.value.map(s => s.currency))]
  return cur.length === 1
})

const fmtAvgCost = computed(() => {
  if (!visibleStats.value.length) return '—'
  if (visibleStats.value.length === 1 || isSingleCurrency.value) {
    const s = visibleStats.value[0]
    const val = showThb.value
      ? toThbVal(s.avg_cost, s.avg_cost_thb, s.currency)
      : toUsdtVal(s.avg_cost, s.currency, s.thb_rate)
    return fmt(val)
  }
  // Mixed: show THB-converted avg across all
  const totalCoins = visibleStats.value.reduce((sum, s) => sum + s.total_coins, 0)
  return totalCoins > 0 ? fmt(totalInvestedThb.value / totalCoins) : '—'
})
const avgCostSub = computed(() => {
  if (!visibleStats.value.length) return ''
  if (visibleStats.value.length === 1) return showThb.value ? 'THB' : visibleStats.value[0].currency
  return 'THB (avg)'
})

const pnlPct = computed(() => {
  const pct = totalInvestedForPct.value > 0 ? (totalPnlThb.value / totalInvestedForPct.value) * 100 : 0
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%`
})
const activePlans = computed(() => plans.value.filter(p => p.status === 'active').length)

const rateSeries = computed(() => [{
  name: 'THB/USDT',
  data: rateData.value.map((r: any) => ({ x: new Date(r.recorded_at.endsWith('Z') ? r.recorded_at : r.recorded_at + 'Z').getTime(), y: parseFloat(r.rate) })),
}])

const rateChartOptions = {
  chart: { background: 'transparent', toolbar: { show: false } },
  theme: { mode: 'dark' },
  stroke: { curve: 'smooth', width: 2 },
  xaxis: { type: 'datetime', labels: { style: { colors: '#9ca3af' } } },
  yaxis: { labels: { style: { colors: '#9ca3af' } } },
  grid: { borderColor: '#374151' },
  colors: ['#6366f1'],
  tooltip: {
    x: { format: 'dd MMM HH:mm' },
    y: { formatter: (val: number) => `${val.toFixed(2)} THB` },
  },
}

async function loadStats() {
  const params = selectedPlanId.value ? { plan_id: selectedPlanId.value } : {}
  stats.value = await statsStore.load(params)
}

async function loadRates() {
  const res = await ratesApi.list(rateDays.value)
  rateData.value = res.data
}

async function loadRecent() {
  const res = await ordersApi.list({ limit: 10, sort_by: 'executed_at', sort_dir: 'desc' })
  recentOrders.value = res.data
}

async function loadPlans() {
  const res = await plansApi.list()
  plans.value = res.data
}

onMounted(async () => {
  await Promise.all([loadPlans(), loadStats(), loadRates(), loadRecent()])
})

watch(selectedPlanId, loadStats)
watch(rateDays, loadRates)

function fmt(v: number) { return v.toLocaleString('en-US', { maximumFractionDigits: 2, minimumFractionDigits: 2 }) }
function fmtPnl(v: number) { return `${v >= 0 ? '+' : ''}${fmt(v)}` }

function planPnlPct(s: any): string {
  const pct = s.unrealized_pnl_pct ?? 0
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(2)}`
}

function toUsdtVal(nativeVal: number, currency: string, planRate?: number): number {
  if (currency !== 'THB') return nativeVal
  const rate = currentRate.value || planRate || 1
  return nativeVal / rate
}

function displayVal(nativeVal: number, thbVal: number, currency = 'USDT', planRate?: number): number {
  if (showThb.value) return toThbVal(nativeVal, thbVal, currency)
  return toUsdtVal(nativeVal, currency, planRate)
}
function displayCur(currency: string): string {
  return showThb.value ? 'THB' : (currency === 'THB' ? 'USDT' : currency)
}

const copiedId = ref<string | null>(null)
function copyPlanJson(s: any) {
  const rate = currentRate.value || s.thb_rate || 1
  const payload = {
    name: s.name,
    exchange: s.exchange,
    symbol: s.symbol,
    currency: s.currency,
    thb_usd_rate: rate,
    total_invested: s.total_invested,
    total_invested_thb: toThb(s.total_invested, s.currency),
    avg_cost: s.avg_cost,
    avg_cost_thb: toThb(s.avg_cost, s.currency),
    current_price: s.current_price,
    current_price_thb: toThb(s.current_price, s.currency),
    total_coins: s.total_coins,
    unrealized_pnl: s.unrealized_pnl,
    unrealized_pnl_thb: toThb(s.unrealized_pnl, s.currency),
    unrealized_pnl_pct: s.unrealized_pnl_pct,
    order_count: s.order_count,
  }
  navigator.clipboard.writeText(JSON.stringify(payload, null, 2))
  copiedId.value = s.plan_id
  setTimeout(() => copiedId.value = null, 2000)
}
</script>
