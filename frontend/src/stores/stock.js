import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'
import { useWatchlistStore } from '@/stores/watchlist'

export const useStockStore = defineStore('stock', () => {
  // State
  const products = ref([])
  const total = ref(0)
  const page = ref(0)
  const size = ref(40)
  const isLoading = ref(false)
  const facets = ref({
    provider: [],
    region: [],
    line: [],
    cycle: [],
    currency: [],
  })

  const stats = ref({
    total_products: 0,
    in_stock_products: 0,
    out_of_stock_products: 0,
    total_subscriptions: 0,
    unique_subscribers: 0,
    total_alerts_sent: 0,
    provider_count: 0,
    online_users: 18,
    today_pv: 3260,
    total_pv: 214890,
  })

  // Filters
  const filters = ref({
    q: '',
    stock: '', // '' | 'in_stock' | 'out_of_stock'
    recommended: false,
    onlyWatched: false,
    providers: [],
    regions: [],
    lines: [],
    cycles: [],
    currencies: [],
    price_min: null,
    price_max: null,
    cpu_min: null,
    ram_min: null,
    disk_min: null,
    traffic_min: null,
    port_min: null,
    sort: 'value', // 'value' | 'price' | '-price' | 'cpu' | 'ram' | 'clicks'
    viewMode: localStorage.getItem('vps_view_mode') || 'table', // 'table' | 'grid'
  })

  function setViewMode(mode) {
    filters.value.viewMode = mode
    localStorage.setItem('vps_view_mode', mode)
  }

  function resetFilters() {
    filters.value.q = ''
    filters.value.stock = ''
    filters.value.recommended = false
    filters.value.onlyWatched = false
    filters.value.providers = []
    filters.value.regions = []
    filters.value.lines = []
    filters.value.cycles = []
    filters.value.currencies = []
    filters.value.price_min = null
    filters.value.price_max = null
    filters.value.cpu_min = null
    filters.value.ram_min = null
    filters.value.disk_min = null
    filters.value.traffic_min = null
    filters.value.port_min = null
    filters.value.sort = 'value'
    page.value = 0
    fetchProducts()
  }

  const activeFilterCount = computed(() => {
    let count = 0
    if (filters.value.q) count++
    if (filters.value.stock) count++
    if (filters.value.recommended) count++
    if (filters.value.onlyWatched) count++
    if (filters.value.providers.length) count += filters.value.providers.length
    if (filters.value.regions.length) count += filters.value.regions.length
    if (filters.value.lines.length) count += filters.value.lines.length
    if (filters.value.cycles.length) count += filters.value.cycles.length
    if (filters.value.currencies.length) count += filters.value.currencies.length
    if (filters.value.price_min !== null || filters.value.price_max !== null) count++
    if (filters.value.cpu_min !== null) count++
    if (filters.value.ram_min !== null) count++
    if (filters.value.disk_min !== null) count++
    if (filters.value.traffic_min !== null) count++
    if (filters.value.port_min !== null) count++
    return count
  })

  async function fetchStats() {
    try {
      const data = await api.getStats()
      stats.value = data
    } catch (err) {
      console.warn('Failed to fetch stats:', err)
    }
  }

  async function fetchFacets() {
    try {
      const data = await api.getFacets()
      facets.value = data
    } catch (err) {
      console.warn('Failed to fetch facets:', err)
    }
  }

  async function fetchProducts(loadMore = false) {
    isLoading.value = true
    try {
      const watchlistStore = useWatchlistStore()
      let idsFilter = undefined
      if (filters.value.onlyWatched) {
        const watched = watchlistStore.watchedProductIds
        if (watched.length === 0) {
          products.value = []
          total.value = 0
          isLoading.value = false
          return
        }
        idsFilter = watched.join(',')
      }

      const params = {
        q: filters.value.q,
        ids: idsFilter,
        stock: filters.value.stock,
        recommended: filters.value.recommended ? true : undefined,
        provider: filters.value.providers.join(','),
        region: filters.value.regions.join(','),
        line: filters.value.lines.join(','),
        cycle: filters.value.cycles.join(','),
        currency: filters.value.currencies.join(','),
        price_min: filters.value.price_min,
        price_max: filters.value.price_max,
        cpu_min: filters.value.cpu_min,
        ram_min: filters.value.ram_min,
        disk_min: filters.value.disk_min,
        traffic_min: filters.value.traffic_min,
        port_min: filters.value.port_min,
        sort: filters.value.sort,
        page: loadMore ? page.value + 1 : 0,
        size: size.value,
      }

      const res = await api.getProducts(params)
      if (loadMore) {
        products.value = [...products.value, ...res.products]
        page.value += 1
      } else {
        products.value = res.products
        page.value = 0
      }
      total.value = res.total
    } catch (err) {
      console.error('Failed to fetch products:', err)
    } finally {
      isLoading.value = false
    }
  }

  return {
    products,
    total,
    page,
    size,
    isLoading,
    facets,
    stats,
    filters,
    activeFilterCount,
    setViewMode,
    resetFilters,
    fetchStats,
    fetchFacets,
    fetchProducts,
  }
})
