<template>
  <div>
    <p class="text-xs text-gray-400 mb-3 font-medium uppercase tracking-wide">Schedule</p>

    <!-- Repeat mode -->
    <div class="grid grid-cols-4 gap-2 mb-4">
      <button v-for="m in modes" :key="m.id" type="button"
        @click="setMode(m.id)"
        :class="mode === m.id ? 'border-indigo-500 bg-indigo-500/10 text-white' : 'border-gray-700 text-gray-400 hover:border-gray-500'"
        class="border rounded-xl py-2.5 text-xs font-medium transition-all flex flex-col items-center gap-1">
        <span class="text-lg">{{ m.icon }}</span>
        {{ m.label }}
      </button>
    </div>

    <!-- Hour mode: every N hours -->
    <div v-if="mode === 'hours'" class="mb-4">
      <p class="text-xs text-gray-500 mb-2">Every N hours</p>
      <div class="flex gap-2 flex-wrap">
        <button v-for="h in [1,2,4,6,8,12]" :key="h" type="button"
          @click="everyHours = h"
          :class="everyHours === h ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-gray-500'"
          class="border rounded-lg px-3 py-1.5 text-sm transition-colors">
          {{ h }}h
        </button>
      </div>
    </div>

    <!-- Day of week (weekly mode) -->
    <div v-if="mode === 'weekly'" class="mb-4">
      <p class="text-xs text-gray-500 mb-2">Day of week</p>
      <div class="flex gap-2">
        <button v-for="d in days" :key="d.val" type="button"
          @click="dow = d.val"
          :class="dow === d.val ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-gray-500'"
          class="border rounded-lg flex-1 py-2 text-xs font-medium transition-colors">
          {{ d.label }}
        </button>
      </div>
    </div>

    <!-- Day of month (monthly mode) -->
    <div v-if="mode === 'monthly'" class="mb-4">
      <p class="text-xs text-gray-500 mb-2">Day of month</p>
      <div class="flex gap-2 flex-wrap">
        <button v-for="d in [1,5,10,15,20,25,28]" :key="d" type="button"
          @click="dom = d"
          :class="dom === d ? 'bg-indigo-600 text-white border-indigo-500' : 'bg-gray-800 text-gray-300 border-gray-700 hover:border-gray-500'"
          class="border rounded-lg px-3 py-1.5 text-sm transition-colors">
          {{ d }}
        </button>
        <input v-model.number="dom" type="number" min="1" max="28" placeholder="Day"
          class="border border-gray-700 bg-gray-800 rounded-lg px-2 py-1.5 text-sm text-gray-100 w-20 focus:outline-none focus:border-indigo-500" />
      </div>
    </div>

    <!-- Time picker (not for hourly) -->
    <div v-if="mode !== 'hours'" class="mb-4">
      <p class="text-xs text-gray-500 mb-2">Time</p>
      <div class="flex items-center gap-3 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3">
        <!-- Hour scroll -->
        <div class="flex flex-col items-center">
          <button type="button" @click="hh = (hh + 1) % 24" class="text-gray-400 hover:text-white text-lg leading-none">▲</button>
          <span class="text-2xl font-mono font-bold text-white w-10 text-center">{{ pad(hh) }}</span>
          <button type="button" @click="hh = (hh - 1 + 24) % 24" class="text-gray-400 hover:text-white text-lg leading-none">▼</button>
        </div>
        <span class="text-2xl text-gray-500 font-bold">:</span>
        <!-- Minute scroll -->
        <div class="flex flex-col items-center">
          <button type="button" @click="mm = (mm + 5) % 60" class="text-gray-400 hover:text-white text-lg leading-none">▲</button>
          <span class="text-2xl font-mono font-bold text-white w-10 text-center">{{ pad(mm) }}</span>
          <button type="button" @click="mm = (mm - 5 + 60) % 60" class="text-gray-400 hover:text-white text-lg leading-none">▼</button>
        </div>
        <!-- Quick time presets -->
        <div class="ml-auto flex flex-col gap-1">
          <button v-for="t in timePresets" :key="t.label" type="button"
            @click="hh = t.h; mm = t.m"
            :class="hh === t.h && mm === t.m ? 'bg-indigo-600 text-white' : 'bg-gray-700 text-gray-300 hover:bg-gray-600'"
            class="rounded px-2 py-0.5 text-xs transition-colors">
            {{ t.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Summary + cron preview -->
    <div class="bg-gray-800/60 border border-gray-700 rounded-lg px-4 py-2.5 flex items-center justify-between">
      <span class="text-sm text-gray-300">{{ summary }}</span>
      <span class="text-xs font-mono text-gray-500">{{ modelValue }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: string): void }>()

type Mode = 'daily' | 'weekly' | 'monthly' | 'hours'

const modes = [
  { id: 'daily' as Mode,   icon: '☀️', label: 'Daily' },
  { id: 'weekly' as Mode,  icon: '📅', label: 'Weekly' },
  { id: 'monthly' as Mode, icon: '🗓️', label: 'Monthly' },
  { id: 'hours' as Mode,   icon: '⏱️', label: 'Every Nh' },
]

const days = [
  { val: 1, label: 'Mon' },
  { val: 2, label: 'Tue' },
  { val: 3, label: 'Wed' },
  { val: 4, label: 'Thu' },
  { val: 5, label: 'Fri' },
  { val: 6, label: 'Sat' },
  { val: 0, label: 'Sun' },
]

const timePresets = [
  { label: '09:00', h: 9, m: 0 },
  { label: '12:00', h: 12, m: 0 },
  { label: '21:00', h: 21, m: 0 },
]

const mode = ref<Mode>('daily')
const hh = ref(9)
const mm = ref(0)
const dow = ref(1)
const dom = ref(1)
const everyHours = ref(4)

function pad(n: number) { return String(n).padStart(2, '0') }

const cron = computed(() => {
  if (mode.value === 'hours') return `0 */${everyHours.value} * * *`
  if (mode.value === 'daily')   return `${mm.value} ${hh.value} * * *`
  if (mode.value === 'weekly')  return `${mm.value} ${hh.value} * * ${dow.value}`
  if (mode.value === 'monthly') return `${mm.value} ${hh.value} ${dom.value} * *`
  return `${mm.value} ${hh.value} * * *`
})

const dayNames: Record<number, string> = { 0: 'Sunday', 1: 'Monday', 2: 'Tuesday', 3: 'Wednesday', 4: 'Thursday', 5: 'Friday', 6: 'Saturday' }

const summary = computed(() => {
  if (mode.value === 'hours') return `Every ${everyHours.value} hours`
  const t = `${pad(hh.value)}:${pad(mm.value)}`
  if (mode.value === 'daily')   return `Every day at ${t}`
  if (mode.value === 'weekly')  return `Every ${dayNames[dow.value]} at ${t}`
  if (mode.value === 'monthly') return `Day ${dom.value} of every month at ${t}`
  return t
})

watch(cron, (v) => emit('update:modelValue', v), { immediate: true })

function parseCron(c: string) {
  if (!c) return
  const parts = c.split(' ')
  if (parts.length !== 5) return
  const [minStr, hourStr, domStr, , dowStr] = parts
  if (hourStr.startsWith('*/')) {
    mode.value = 'hours'
    everyHours.value = parseInt(hourStr.slice(2)) || 4
    return
  }
  mm.value = parseInt(minStr) || 0
  hh.value = parseInt(hourStr) || 9
  if (domStr !== '*') { mode.value = 'monthly'; dom.value = parseInt(domStr) || 1 }
  else if (dowStr !== '*') { mode.value = 'weekly'; dow.value = parseInt(dowStr) }
  else { mode.value = 'daily' }
}

function setMode(m: Mode) { mode.value = m }

parseCron(props.modelValue)
watch(() => props.modelValue, (v) => { if (v !== cron.value) parseCron(v) })
</script>
