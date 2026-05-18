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
    </nav>

    <!-- Main content -->
    <main class="flex-1 ml-56 p-8">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
const nav = [
  { path: '/', icon: '📊', label: 'Dashboard' },
  { path: '/plans', icon: '📋', label: 'DCA Plans' },
  { path: '/orders', icon: '📦', label: 'Orders' },
  { path: '/settings', icon: '⚙️', label: 'Settings' },
]
</script>
