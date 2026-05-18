<template>
  <div>
    <label class="block text-sm text-gray-400 mb-1">{{ label }}</label>
    <input
      :type="type ?? 'text'"
      :value="modelValue"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      :placeholder="placeholder"
      :required="required"
      class="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-100 focus:outline-none focus:border-indigo-500"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{ label: string; modelValue: any; placeholder?: string; type?: string; required?: boolean }>()
defineEmits(['update:modelValue'])
</script>
