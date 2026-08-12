<template>
  <div class="w-full border-b border-border/60 bg-secondary/30 py-2">
    <div class="max-w-[1600px] mx-auto px-3 sm:px-6 flex items-center justify-between gap-4">
      <!-- Quick Filter Pills -->
      <div class="flex items-center gap-1.5 overflow-x-auto no-scrollbar py-0.5 text-xs">
        <button
          @click="selectQuickTag('all')"
          class="px-2.5 py-1 rounded-full border transition-all whitespace-nowrap font-medium"
          :class="isQuickTagActive('all') ? 'bg-primary text-primary-foreground border-primary' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
        >
          全部机型
        </button>

        <button
          @click="toggleStockOnly"
          class="px-2.5 py-1 rounded-full border transition-all whitespace-nowrap font-medium flex items-center gap-1"
          :class="stockStore.filters.stock === 'in_stock' ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
          仅有货在售
        </button>

        <button
          @click="toggleRecommended"
          class="px-2.5 py-1 rounded-full border transition-all whitespace-nowrap font-medium flex items-center gap-1"
          :class="stockStore.filters.recommended ? 'bg-amber-500 text-white border-amber-500' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
        >
          <span>⭐</span>
          仅推荐
        </button>

        <span class="h-3.5 w-px bg-border mx-1"></span>

        <!-- Line Quick Filters -->
        <button
          v-for="line in ['CN2 GIA', 'AS9929', 'CMIN2', 'AS4837']"
          :key="line"
          @click="toggleLineFilter(line)"
          class="px-2 py-0.8 rounded-full border transition-all whitespace-nowrap"
          :class="stockStore.filters.lines.includes(line) ? 'bg-primary/20 text-primary border-primary font-semibold' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
        >
          {{ line }}
        </button>

        <span class="h-3.5 w-px bg-border mx-1"></span>

        <!-- Provider Quick Filters -->
        <button
          v-for="prov in ['搬瓦工 BandwagonHost', 'RackNerd', 'DMIT', 'ClawCloud', 'V.PS', 'Netcup']"
          :key="prov"
          @click="toggleProviderFilter(prov)"
          class="px-2 py-0.8 rounded-full border transition-all whitespace-nowrap"
          :class="stockStore.filters.providers.includes(prov) ? 'bg-primary/20 text-primary border-primary font-semibold' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
        >
          {{ prov.split(' ')[0] }}
        </button>
      </div>

      <!-- Live Broadcast / Announcement -->
      <div class="hidden xl:flex items-center gap-2 text-xs text-muted-foreground shrink-0 font-medium">
        <span class="flex h-2 w-2 relative">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
        </span>
        <span class="truncate max-w-[280px]">实时监控中 · 关注心仪机型有货降价邮件送达</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useStockStore } from '@/stores/stock'

const stockStore = useStockStore()

function isQuickTagActive(type) {
  if (type === 'all') {
    return (
      !stockStore.filters.stock &&
      !stockStore.filters.recommended &&
      stockStore.filters.lines.length === 0 &&
      stockStore.filters.providers.length === 0
    )
  }
  return false
}

function selectQuickTag(type) {
  if (type === 'all') {
    stockStore.resetFilters()
  }
}

function toggleStockOnly() {
  stockStore.filters.stock = stockStore.filters.stock === 'in_stock' ? '' : 'in_stock'
  stockStore.fetchProducts()
}

function toggleRecommended() {
  stockStore.filters.recommended = !stockStore.filters.recommended
  stockStore.fetchProducts()
}

function toggleLineFilter(line) {
  const idx = stockStore.filters.lines.indexOf(line)
  if (idx >= 0) {
    stockStore.filters.lines.splice(idx, 1)
  } else {
    stockStore.filters.lines.push(line)
  }
  stockStore.fetchProducts()
}

function toggleProviderFilter(prov) {
  const idx = stockStore.filters.providers.indexOf(prov)
  if (idx >= 0) {
    stockStore.filters.providers.splice(idx, 1)
  } else {
    stockStore.filters.providers.push(prov)
  }
  stockStore.fetchProducts()
}
</script>

<style scoped>
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
