<template>
  <div class="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
    <div class="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-md shadow-2xl">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <div>
          <h2 class="text-base font-semibold text-red-400">Sell Token</h2>
          <p class="text-xs text-gray-500 mt-0.5">{{ plan.name }} · {{ plan.exchange.toUpperCase() }} · {{ plan.symbol }}</p>
        </div>
        <button @click="$emit('close')" class="text-gray-500 hover:text-gray-300 text-xl leading-none">&times;</button>
      </div>

      <div class="px-6 py-5 flex flex-col gap-5">
        <!-- Order type tabs -->
        <div class="grid grid-cols-3 gap-2">
          <button v-for="t in types" :key="t.id" type="button"
            @click="orderType = t.id"
            :class="orderType === t.id ? 'border-red-500 bg-red-500/10 text-red-300' : 'border-gray-700 text-gray-400 hover:border-gray-500'"
            class="border rounded-xl py-3 text-sm font-medium transition-all flex flex-col items-center gap-1">
            <span class="text-xl">{{ t.icon }}</span>
            {{ t.label }}
            <span class="text-xs opacity-60">{{ t.desc }}</span>
          </button>
        </div>

        <!-- Market / Limit: amount in base token -->
        <div v-if="orderType !== 'percent'">
          <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">
            จำนวน {{ baseToken }} ที่ต้องการขาย
          </p>
          <div class="flex gap-2 items-center">
            <input v-model.number="baseAmount" type="number" min="0" step="any" placeholder="0.00"
              class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-lg text-gray-100 font-mono focus:outline-none focus:border-red-500" />
            <span class="text-gray-400 font-medium w-16 text-center text-sm">{{ baseToken }}</span>
          </div>
          <!-- Quick percent shortcuts -->
          <div class="flex gap-2 mt-2">
            <button v-for="pct in [25, 50, 75, 100]" :key="pct" type="button"
              @click="setPercent(pct)"
              class="flex-1 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg py-1.5 text-xs text-gray-300 transition-colors">
              {{ pct }}%
            </button>
          </div>
          <p class="text-xs text-gray-600 mt-1">Holdings: {{ fmt(holdings, 8) }} {{ baseToken }}</p>
        </div>

        <!-- Percent: slider -->
        <div v-if="orderType === 'percent'">
          <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">เปอร์เซ็นต์ที่ต้องการขาย</p>
          <div class="flex items-center gap-4 mb-3">
            <input v-model.number="sellPercent" type="range" min="1" max="100" step="1" class="flex-1 accent-red-500" />
            <div class="flex items-center gap-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 w-20">
              <input v-model.number="sellPercent" type="number" min="1" max="100"
                class="w-10 bg-transparent text-white text-sm text-right focus:outline-none" />
              <span class="text-gray-400 text-sm">%</span>
            </div>
          </div>
          <div class="flex gap-2">
            <button v-for="pct in [25, 50, 75, 100]" :key="pct" type="button"
              @click="sellPercent = pct"
              :class="sellPercent === pct ? 'bg-red-600 text-white border-red-500' : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-gray-500'"
              class="flex-1 border rounded-lg py-1.5 text-sm font-medium transition-colors">
              {{ pct }}%
            </button>
          </div>
          <p class="text-xs text-gray-500 mt-2">
            จะขาย ≈ {{ fmt(holdings * sellPercent / 100, 8) }} {{ baseToken }}
            จาก {{ fmt(holdings, 8) }} {{ baseToken }}
          </p>
        </div>

        <!-- Limit price -->
        <div v-if="orderType === 'limit'">
          <p class="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">ราคาที่ต้องการขาย ({{ quoteToken }})</p>
          <div class="flex gap-2 items-center">
            <input v-model.number="limitPrice" type="number" min="0" step="any" :placeholder="`ราคาปัจจุบัน: ${fmt(currentPrice)}`"
              class="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2.5 text-lg text-gray-100 font-mono focus:outline-none focus:border-red-500" />
            <span class="text-gray-400 font-medium w-16 text-center text-sm">{{ quoteToken }}</span>
          </div>
          <div class="flex gap-2 mt-2">
            <button v-for="pct in [-5, -2, 0, 2, 5]" :key="pct" type="button"
              @click="limitPrice = parseFloat((currentPrice * (1 + pct/100)).toFixed(4))"
              :class="pct > 0 ? 'text-green-400 border-green-900' : pct < 0 ? 'text-red-400 border-red-900' : 'text-gray-300 border-gray-700'"
              class="flex-1 bg-gray-800 border rounded-lg py-1.5 text-xs transition-colors hover:bg-gray-700">
              {{ pct >= 0 ? '+' : '' }}{{ pct }}%
            </button>
          </div>
        </div>

        <!-- Order summary -->
        <div class="bg-gray-800/60 border border-gray-700 rounded-xl px-4 py-3 text-sm flex flex-col gap-1.5">
          <div class="flex justify-between text-gray-400">
            <span>ประเภท</span><span class="text-white">{{ orderType.toUpperCase() }}</span>
          </div>
          <div class="flex justify-between text-gray-400">
            <span>จำนวนที่ขาย</span>
            <span class="text-white font-mono">{{ fmt(sellQty, 8) }} {{ baseToken }}</span>
          </div>
          <div v-if="orderType !== 'percent'" class="flex justify-between text-gray-400">
            <span>ราคาปัจจุบัน</span>
            <span class="text-yellow-300 font-mono">{{ fmt(currentPrice) }} {{ quoteToken }}</span>
          </div>
          <div class="flex justify-between text-gray-400 border-t border-gray-700 pt-1.5 mt-0.5">
            <span>รับโดยประมาณ</span>
            <span class="text-green-400 font-mono font-semibold">≈ {{ fmt(estimatedReceive) }} {{ quoteToken }}</span>
          </div>
        </div>

        <!-- Action buttons -->
        <div class="flex gap-3">
          <button type="button" @click="$emit('close')" class="flex-1 bg-gray-800 hover:bg-gray-700 text-gray-300 py-2.5 rounded-xl text-sm transition-colors">Cancel</button>
          <button type="button" @click="confirm" :disabled="!canSubmit || loading"
            class="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-40 disabled:cursor-not-allowed text-white py-2.5 rounded-xl text-sm font-medium transition-colors">
            {{ loading ? 'กำลังส่งคำสั่ง...' : `Sell ${baseToken}` }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Confirm dialog -->
  <div v-if="showConfirm" class="fixed inset-0 bg-black/80 flex items-center justify-center z-[60] p-4">
    <div class="bg-gray-900 border border-red-700 rounded-2xl p-6 w-full max-w-sm text-center shadow-2xl">
      <div class="text-4xl mb-3">⚠️</div>
      <p class="font-semibold text-lg mb-1">ยืนยันการขาย</p>
      <p class="text-gray-400 text-sm mb-2">{{ plan.symbol }} · {{ plan.exchange.toUpperCase() }}</p>
      <p class="text-red-300 text-sm mb-1">ขาย <b>{{ fmt(sellQty, 8) }} {{ baseToken }}</b></p>
      <p class="text-green-400 text-sm mb-5">รับโดยประมาณ <b>{{ fmt(estimatedReceive) }} {{ quoteToken }}</b></p>
      <div class="flex gap-3">
        <button @click="showConfirm = false" class="flex-1 bg-gray-800 hover:bg-gray-700 py-2.5 rounded-xl text-sm transition-colors">ยกเลิก</button>
        <button @click="submit" class="flex-1 bg-red-600 hover:bg-red-700 text-white py-2.5 rounded-xl text-sm font-medium transition-colors">ยืนยันขาย</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ordersApi, statsApi, ratesApi } from '../api'

const props = defineProps<{ plan: any }>()
const emit = defineEmits<{ (e: 'close'): void; (e: 'done'): void }>()

type OrderType = 'market' | 'limit' | 'percent'
const types = [
  { id: 'market' as OrderType,  icon: '⚡', label: 'Market', desc: 'ราคาตลาด' },
  { id: 'limit' as OrderType,   icon: '🎯', label: 'Limit',  desc: 'กำหนดราคา' },
  { id: 'percent' as OrderType, icon: '%',  label: 'Percent', desc: '% ของ holdings' },
]

const orderType = ref<OrderType>('market')
const baseAmount = ref<number>(0)
const sellPercent = ref<number>(25)
const limitPrice = ref<number>(0)
const currentPrice = ref<number>(0)
const holdings = ref<number>(0)
const loading = ref(false)
const showConfirm = ref(false)

const baseToken = computed(() => props.plan.symbol.split('/')[0])
const quoteToken = computed(() => props.plan.symbol.split('/')[1])

const sellQty = computed(() => {
  if (orderType.value === 'percent') return holdings.value * sellPercent.value / 100
  return baseAmount.value || 0
})

const priceToUse = computed(() => orderType.value === 'limit' && limitPrice.value ? limitPrice.value : currentPrice.value)
const estimatedReceive = computed(() => sellQty.value * priceToUse.value)

const canSubmit = computed(() => {
  if (sellQty.value <= 0) return false
  if (orderType.value === 'limit' && !limitPrice.value) return false
  return true
})

function fmt(v: number, dp = 2) { return v.toLocaleString('en-US', { maximumFractionDigits: dp, minimumFractionDigits: dp }) }

function setPercent(pct: number) {
  baseAmount.value = parseFloat((holdings.value * pct / 100).toFixed(8))
}

function confirm() { showConfirm.value = true }

async function submit() {
  showConfirm.value = false
  loading.value = true
  try {
    await ordersApi.sell({
      plan_id: props.plan.id,
      order_type: orderType.value,
      base_amount: orderType.value !== 'percent' ? sellQty.value : undefined,
      percent: orderType.value === 'percent' ? sellPercent.value : undefined,
      limit_price: orderType.value === 'limit' ? limitPrice.value : undefined,
    })
    emit('done')
  } catch (e: any) {
    alert('Sell failed: ' + (e?.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  // Load current price
  try {
    const res = await statsApi.summary({ plan_id: props.plan.id })
    const stat = res.data[0]
    if (stat) { currentPrice.value = stat.current_price; holdings.value = stat.total_coins }
  } catch {}
  if (!limitPrice.value && currentPrice.value) limitPrice.value = parseFloat(currentPrice.value.toFixed(4))
})
</script>
