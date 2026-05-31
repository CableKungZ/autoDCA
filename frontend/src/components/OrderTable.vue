<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="text-gray-400 border-b border-gray-800">
          <th class="text-left py-2 pr-4">Date</th>
          <th class="text-left py-2 pr-4">Exchange</th>
          <th class="text-left py-2 pr-4">Pair</th>
          <th v-if="!compact" class="text-right py-2 pr-4">Spent</th>
          <th class="text-right py-2 pr-4">Received</th>
          <th class="text-right py-2 pr-4">Price</th>
          <th v-if="!compact" class="text-right py-2 pr-4">Cost/Token</th>
          <th v-if="!compact" class="text-right py-2 pr-4">THB Rate</th>
          <th class="text-left py-2">Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!orders.length">
          <td :colspan="compact ? 5 : 9" class="text-center text-gray-500 py-8">No orders yet</td>
        </tr>
        <tr v-for="o in orders" :key="o.id" class="border-b border-gray-800/50 hover:bg-gray-800/30">
          <td class="py-2 pr-4 text-gray-400">{{ fmtDate(o.executed_at) }}</td>
          <td class="py-2 pr-4 capitalize">{{ o.exchange }}</td>
          <td class="py-2 pr-4 font-mono">{{ o.symbol }}</td>
          <td v-if="!compact" class="py-2 pr-4 text-right">{{ fmtSpent(o) }}</td>
          <td class="py-2 pr-4 text-right font-mono">
            <span v-if="o.base_amount">{{ fmt(o.base_amount, 8) }} <span class="text-gray-500 text-xs">{{ baseToken(o) }}</span></span>
            <span v-else>—</span>
          </td>
          <td class="py-2 pr-4 text-right">{{ fmtPrice(o) }}</td>
          <td v-if="!compact" class="py-2 pr-4 text-right">{{ fmtCostPerToken(o) }}</td>
          <td v-if="!compact" class="py-2 pr-4 text-right text-gray-400">{{ o.thb_usd_rate ? fmt(o.thb_usd_rate, 2) : '—' }}</td>
          <td class="py-2">
            <span :class="statusClass(o.status)" class="px-2 py-0.5 rounded-full text-xs font-medium">
              {{ o.status }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns'

const props = defineProps<{ orders: any[]; compact?: boolean; showThb?: boolean }>()

function fmtDate(d: string) { return format(new Date(d.endsWith('Z') ? d : d + 'Z'), 'dd MMM HH:mm') }
function fmt(v: number, dp = 4) { return v.toLocaleString('en-US', { maximumFractionDigits: dp, minimumFractionDigits: dp }) }

function baseToken(o: any): string {
  return o.symbol?.split('/')[0] ?? ''
}

function nativeCurrency(o: any): string {
  return o.currency || (o.exchange === 'bitkub' ? 'THB' : 'USDT')
}

function toThb(value: number, o: any): number {
  const cur = nativeCurrency(o)
  if (cur === 'THB') return value
  const rate = o.thb_usd_rate || 1
  return value * rate
}

function toUsdt(value: number, o: any): number {
  const cur = nativeCurrency(o)
  if (cur !== 'THB') return value
  const rate = o.thb_usd_rate || 1
  return value / rate
}

function displayCur(o: any): string {
  return props.showThb ? 'THB' : 'USDT'
}

function displayVal(value: number, o: any): number {
  if (props.showThb) return toThb(value, o)
  return toUsdt(value, o)
}

function fmtSpent(o: any): string {
  const amount = parseFloat(o.quote_amount)
  if (!amount) return '—'
  const cur = nativeCurrency(o)
  if (props.showThb) {
    const thb = toThb(amount, o)
    if (cur !== 'THB') return `${fmt(thb, 2)} THB (${fmt(amount, 2)} ${cur})`
    return `${fmt(thb, 2)} THB`
  } else {
    const usdt = toUsdt(amount, o)
    if (cur === 'THB') return `${fmt(usdt, 2)} USDT (${fmt(amount, 2)} THB)`
    return `${fmt(amount, 2)} USDT`
  }
}

function fmtPrice(o: any): string {
  if (!o.price) return '—'
  const val = displayVal(parseFloat(o.price), o)
  const cur = props.showThb ? 'THB' : (nativeCurrency(o) === 'THB' ? 'USDT' : nativeCurrency(o))
  return `${fmt(val, 4)} ${cur}`
}

function fmtCostPerToken(o: any): string {
  if (!o.cost_per_token) return '—'
  const val = displayVal(parseFloat(o.cost_per_token), o)
  const cur = props.showThb ? 'THB' : (nativeCurrency(o) === 'THB' ? 'USDT' : nativeCurrency(o))
  return `${fmt(val, 4)} ${cur}`
}

function statusClass(s: string) {
  return {
    filled: 'bg-green-900 text-green-300',
    pending: 'bg-yellow-900 text-yellow-300',
    failed: 'bg-red-900 text-red-300',
    cancelled: 'bg-gray-700 text-gray-300',
  }[s] ?? 'bg-gray-700 text-gray-300'
}
</script>
