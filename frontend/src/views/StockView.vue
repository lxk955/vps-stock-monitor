<template>
  <div class="min-h-screen bg-background text-foreground flex flex-col font-sans">
    <!-- 1. Navbar -->
    <Navbar
      @open-search="showSearchModal = true"
      @open-watchlist="showWatchlistModal = true"
      @open-admin="showAdminModal = true"
      @open-community="openCommunityModal"
    />

    <!-- 2. Quick Ticker Bar -->
    <TickerBar />

    <!-- 3. Main Content Container -->
    <main class="max-w-[1600px] w-full mx-auto px-3 sm:px-6 py-4 sm:py-6 flex-1 flex flex-col lg:flex-row gap-5">
      <!-- Left: Multi-dimensional Filter Sidebar -->
      <FilterSidebar />

      <!-- Right: Main Product Listing Area (Exact layout from panel.yins.win) -->
      <section class="flex-1 min-w-0 space-y-4">
        <!-- Control Header: Result Count, Sort Dropdown & View Mode Switcher -->
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-card border border-border/80 shadow-xs text-xs">
          <!-- Left: Count indicator -->
          <div class="flex items-center gap-2 font-medium text-muted-foreground">
            <span>共 <strong class="text-foreground font-bold">{{ filteredProducts.length }}</strong> 个结果（已筛选）</span>
            <span class="text-border">·</span>
            <span>{{ stockStore.filters.viewMode === 'table' ? '表格视图' : '网格视图' }}</span>
          </div>

          <!-- Right: Sort Select & View Mode Toggle -->
          <div class="flex items-center gap-2.5">
            <!-- Sort Selector -->
            <div class="flex items-center gap-1.5">
              <span class="text-muted-foreground">排序:</span>
              <select
                v-model="stockStore.filters.sort"
                @change="onSortChange"
                class="px-2.5 py-1.5 rounded-lg bg-secondary/60 border border-border text-foreground font-medium text-xs focus:outline-none focus:border-primary"
              >
                <option value="value">性价比 (综合最优)</option>
                <option value="price">价格 (从低到高)</option>
                <option value="-price">价格 (从高到低)</option>
                <option value="cpu">CPU 核心数</option>
                <option value="ram">内存大小</option>
                <option value="clicks">点击热度</option>
              </select>
            </div>

            <!-- View Mode Switcher (Table / Grid) -->
            <div class="flex items-center bg-secondary/80 border border-border/70 rounded-lg p-0.5">
              <button
                @click="stockStore.setViewMode('table')"
                class="p-1.5 rounded-md transition-colors"
                :class="stockStore.filters.viewMode === 'table' ? 'bg-card text-primary shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'"
                title="表格视图"
              >
                <TableIcon class="w-4 h-4" />
              </button>
              <button
                @click="stockStore.setViewMode('grid')"
                class="p-1.5 rounded-md transition-colors"
                :class="stockStore.filters.viewMode === 'grid' ? 'bg-card text-primary shadow-xs font-bold' : 'text-muted-foreground hover:text-foreground'"
                title="网格卡片视图"
              >
                <LayoutGrid class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Products List Area -->
        <div v-if="stockStore.isLoading && stockStore.products.length === 0" class="py-24 text-center text-muted-foreground space-y-2">
          <Loader2 class="w-8 h-8 animate-spin mx-auto text-primary" />
          <p class="text-xs font-medium">正在加载 VPS 实时库存与方案数据...</p>
        </div>

        <div v-else-if="filteredProducts.length === 0" class="py-24 text-center text-muted-foreground space-y-3 bg-card rounded-xl border border-border/60">
          <ServerCrash class="w-10 h-10 mx-auto opacity-40 text-muted-foreground" />
          <div class="space-y-1">
            <p class="text-sm font-bold text-foreground">没有找到符合当前筛选条件的机型</p>
            <p class="text-xs opacity-70">尝试放宽规格、取消线路或厂商限制重新搜索</p>
          </div>
          <button
            @click="stockStore.resetFilters"
            class="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity"
          >
            重置全部筛选
          </button>
        </div>

        <!-- Table View -->
        <ProductTable
          v-else-if="stockStore.filters.viewMode === 'table'"
          :products="filteredProducts"
          @open-watch="openWatchModal"
          @open-history="openHistoryModal"
        />

        <!-- Grid View -->
        <div
          v-else
          class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          <ProductCard
            v-for="product in filteredProducts"
            :key="product.id"
            :product="product"
            @open-watch="openWatchModal"
            @open-history="openHistoryModal"
          />
        </div>

        <!-- Load More / Pagination footer if more available -->
        <div
          v-if="stockStore.products.length < stockStore.total && !stockStore.filters.onlyWatched"
          class="text-center pt-4"
        >
          <button
            @click="stockStore.fetchProducts(true)"
            :disabled="stockStore.isLoading"
            class="px-6 py-2.5 rounded-xl bg-card border border-border hover:bg-secondary text-xs font-bold text-foreground transition-all shadow-xs disabled:opacity-50 inline-flex items-center gap-2"
          >
            <Loader2 v-if="stockStore.isLoading" class="w-3.5 h-3.5 animate-spin" />
            <span>加载更多机型 ({{ stockStore.products.length }} / {{ stockStore.total }})</span>
          </button>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="mt-auto border-t border-border/70 py-6 bg-card text-center text-xs text-muted-foreground">
      <div class="max-w-[1600px] mx-auto px-4 space-y-1.5">
        <p>VPS 实时库存与降价监控平台 · 自动追踪全网 40+ 厂商热门方案库存与价格走势</p>
        <p class="text-[11px] opacity-70">
          快捷键提示：按 <kbd class="px-1.5 py-0.5 bg-secondary rounded border border-border font-mono text-[10px]">⌘K</kbd> 或 <kbd class="px-1.5 py-0.5 bg-secondary rounded border border-border font-mono text-[10px]">/</kbd> 随时唤起全局搜索
        </p>
      </div>
    </footer>

    <!-- Modals -->
    <WatchModal
      v-model:visible="showWatchModal"
      :product="selectedProduct"
      @success="onToastSuccess"
      @error="onToastError"
    />

    <MyWatchlistModal
      v-model:visible="showWatchlistModal"
      @open-watch="openWatchModal"
      @success="onToastSuccess"
      @error="onToastError"
    />

    <PriceHistoryModal
      v-model:visible="showHistoryModal"
      :product="selectedProduct"
    />

    <AdminSettingsModal
      v-model:visible="showAdminModal"
      @success="onToastSuccess"
      @error="onToastError"
    />

    <QuickSearchModal
      v-model:visible="showSearchModal"
      @open-watch="openWatchModal"
    />

    <CommunityModal
      v-model:visible="showCommunityModal"
      :type="communityModalType"
    />

    <!-- Global Toast -->
    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useStockStore } from '@/stores/stock'
import { useWatchlistStore } from '@/stores/watchlist'

import Navbar from '@/components/Navbar.vue'
import TickerBar from '@/components/TickerBar.vue'
import FilterSidebar from '@/components/FilterSidebar.vue'
import ProductTable from '@/components/ProductTable.vue'
import ProductCard from '@/components/ProductCard.vue'
import WatchModal from '@/components/WatchModal.vue'
import MyWatchlistModal from '@/components/MyWatchlistModal.vue'
import PriceHistoryModal from '@/components/PriceHistoryModal.vue'
import AdminSettingsModal from '@/components/AdminSettingsModal.vue'
import QuickSearchModal from '@/components/QuickSearchModal.vue'
import CommunityModal from '@/components/CommunityModal.vue'
import Toast from '@/components/Toast.vue'

import { Table as TableIcon, LayoutGrid, Loader2, ServerCrash } from 'lucide-vue-next'

const stockStore = useStockStore()
const watchlistStore = useWatchlistStore()

// Modals State
const showWatchModal = ref(false)
const showWatchlistModal = ref(false)
const showHistoryModal = ref(false)
const showAdminModal = ref(false)
const showSearchModal = ref(false)
const showCommunityModal = ref(false)
const communityModalType = ref('group')
const selectedProduct = ref(null)

const toastRef = ref(null)

const filteredProducts = computed(() => stockStore.products)

watch(() => stockStore.filters.onlyWatched, () => {
  stockStore.fetchProducts()
})

function openWatchModal(product) {
  selectedProduct.value = product
  showWatchModal.value = true
}

function openHistoryModal(product) {
  selectedProduct.value = product
  showHistoryModal.value = true
}

function openCommunityModal(type) {
  communityModalType.value = type
  showCommunityModal.value = true
}

function onSortChange() {
  stockStore.fetchProducts()
}

function onToastSuccess(msg) {
  toastRef.value?.show(msg, 'success')
}

function onToastError(msg) {
  toastRef.value?.show(msg, 'error')
}

// Global Keyboard Shortcut for Search (Cmd+K or /)
function handleKeydown(e) {
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
    e.preventDefault()
    showSearchModal.value = !showSearchModal.value
  } else if (e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    e.preventDefault()
    showSearchModal.value = true
  }
}

onMounted(async () => {
  window.addEventListener('keydown', handleKeydown)
  await stockStore.fetchStats()
  await stockStore.fetchFacets()
  await stockStore.fetchProducts()
  await watchlistStore.syncRemote()
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>
