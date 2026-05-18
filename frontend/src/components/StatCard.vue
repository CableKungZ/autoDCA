<template>
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
    <p class="text-gray-400 text-sm mb-1">{{ title }}</p>
    <p :class="['text-2xl font-bold', positive === false ? 'text-red-400' : positive === true ? 'text-green-400' : 'text-white']">
      {{ value }}
    </p>
    <p class="text-gray-500 text-xs mt-1">{{ sub }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  value: string
  sub?: string
  positive?: boolean
  color?: string
}>()
</script>
