import { defineStore } from 'pinia'
import { ref } from 'vue'
import { statsApi } from '../api'

const STALE_MS = 30_000 // treat cache stale after 30s

export const useStatsStore = defineStore('stats', () => {
  const stats = ref<any[]>([])
  const lastFetchedAt = ref(0)
  const loading = ref(false)

  async function fetchStats(params: Record<string, any> = {}) {
    const res = await statsApi.summary(params)
    // Only update global cache for unfiltered requests
    if (!params.plan_id) {
      stats.value = res.data
      lastFetchedAt.value = Date.now()
    }
    return res.data
  }

  // Returns cached data immediately, refreshes in background if stale
  async function load(params: Record<string, any> = {}, force = false): Promise<any[]> {
    const isStale = Date.now() - lastFetchedAt.value > STALE_MS
    const isEmpty = stats.value.length === 0

    if (params.plan_id) {
      // Filtered requests always go fresh
      return fetchStats(params)
    }

    if (isEmpty || force) {
      // No cache — must await
      loading.value = true
      try { return await fetchStats() } finally { loading.value = false }
    }

    if (isStale) {
      // Return stale data immediately, refresh silently in background
      fetchStats().catch(() => {})
    }

    return stats.value
  }

  function invalidate() {
    lastFetchedAt.value = 0
  }

  return { stats, loading, load, invalidate }
})
