<template>
  <aside class="w-full lg:w-72 shrink-0 bg-card border border-border/80 rounded-xl p-4 shadow-sm space-y-5 text-sm">
    <!-- Header: Title & Reset Button -->
    <div class="flex items-center justify-between pb-3 border-b border-border/60">
      <div class="flex items-center gap-2 font-bold text-foreground">
        <SlidersHorizontal class="w-4 h-4 text-primary" />
        <span>筛选</span>
        <span v-if="stockStore.activeFilterCount > 0" class="px-1.5 py-0.2 text-[11px] font-bold rounded-full bg-primary/10 text-primary">
          {{ stockStore.activeFilterCount }}
        </span>
      </div>

      <button
        @click="stockStore.resetFilters"
        class="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
        title="重置全部筛选条件"
      >
        <RotateCcw class="w-3.5 h-3.5" />
        <span>重置</span>
      </button>
    </div>

    <!-- Quick Switches (Exact layout from panel.yins.win) -->
    <div class="space-y-2.5 pb-3 border-b border-border/60">
      <label class="flex items-center justify-between cursor-pointer group">
        <span class="text-xs font-medium text-foreground group-hover:text-primary transition-colors flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
          仅有货
        </span>
        <input
          type="checkbox"
          :checked="stockStore.filters.stock === 'in_stock'"
          @change="onStockToggle"
          class="sr-only peer"
        />
        <div class="w-8 h-4 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-primary relative"></div>
      </label>

      <label class="flex items-center justify-between cursor-pointer group">
        <span class="text-xs font-medium text-foreground group-hover:text-primary transition-colors flex items-center gap-1.5">
          <span class="text-amber-500">⭐</span>
          仅推荐
        </span>
        <input
          type="checkbox"
          v-model="stockStore.filters.recommended"
          @change="triggerSearch"
          class="sr-only peer"
        />
        <div class="w-8 h-4 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-primary relative"></div>
      </label>

      <label class="flex items-center justify-between cursor-pointer group">
        <span class="text-xs font-medium text-foreground group-hover:text-primary transition-colors flex items-center gap-1.5">
          <Bell class="w-3.5 h-3.5 text-primary" />
          仅看我关注的
        </span>
        <input
          type="checkbox"
          v-model="stockStore.filters.onlyWatched"
          class="sr-only peer"
        />
        <div class="w-8 h-4 bg-muted peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-primary relative"></div>
      </label>
    </div>

    <!-- Facet Group: 地区 (Region) -->
    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        <span>地区</span>
        <span class="text-[11px] font-mono lowercase">({{ stockStore.facets.region.length }})</span>
      </div>
      <div class="flex flex-wrap gap-1 max-h-36 overflow-y-auto pr-1">
        <button
          v-for="item in stockStore.facets.region"
          :key="item.value"
          @click="toggleItem(stockStore.filters.regions, item.value)"
          class="px-2 py-0.8 rounded-md text-xs border transition-all flex items-center gap-1"
          :class="stockStore.filters.regions.includes(item.value) ? 'bg-primary text-primary-foreground border-primary font-medium' : 'bg-secondary/60 hover:bg-secondary text-muted-foreground border-transparent'"
        >
          <span>{{ item.value }}</span>
          <span class="text-[10px] opacity-70 font-mono">{{ item.count }}</span>
        </button>
      </div>
    </div>

    <!-- Facet Group: 线路 (Line) -->
    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        <span>线路</span>
        <span class="text-[11px] font-mono lowercase">({{ stockStore.facets.line.length }})</span>
      </div>
      <div class="flex flex-wrap gap-1 max-h-36 overflow-y-auto pr-1">
        <button
          v-for="item in stockStore.facets.line"
          :key="item.value"
          @click="toggleItem(stockStore.filters.lines, item.value)"
          class="px-2 py-0.8 rounded-md text-xs border transition-all flex items-center gap-1"
          :class="stockStore.filters.lines.includes(item.value) ? 'bg-primary text-primary-foreground border-primary font-medium' : 'bg-secondary/60 hover:bg-secondary text-muted-foreground border-transparent'"
        >
          <span>{{ item.value }}</span>
          <span class="text-[10px] opacity-70 font-mono">{{ item.count }}</span>
        </button>
      </div>
    </div>

    <!-- Facet Group: 厂商 (Provider) -->
    <div class="space-y-2">
      <div class="flex items-center justify-between text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        <span>厂商</span>
        <span class="text-[11px] font-mono lowercase">({{ stockStore.facets.provider.length }})</span>
      </div>
      <div class="flex flex-wrap gap-1 max-h-40 overflow-y-auto pr-1">
        <button
          v-for="item in stockStore.facets.provider"
          :key="item.value"
          @click="toggleItem(stockStore.filters.providers, item.value)"
          class="px-2 py-0.8 rounded-md text-xs border transition-all flex items-center gap-1"
          :class="stockStore.filters.providers.includes(item.value) ? 'bg-primary text-primary-foreground border-primary font-medium' : 'bg-secondary/60 hover:bg-secondary text-muted-foreground border-transparent'"
        >
          <span class="truncate max-w-[120px]">{{ item.value.split(' ')[0] }}</span>
          <span class="text-[10px] opacity-70 font-mono">{{ item.count }}</span>
        </button>
      </div>
    </div>

    <!-- Specs & Price Inputs (Exact matching panel.yins.win) -->
    <div class="space-y-3 pt-2 border-t border-border/60">
      <div class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        规格 / 价格
      </div>

      <!-- Price Range -->
      <div class="space-y-1">
        <label class="text-[11px] text-muted-foreground">价格区间 ($)</label>
        <div class="flex items-center gap-1.5">
          <input
            type="number"
            placeholder="Min"
            v-model.number="stockStore.filters.price_min"
            @change="triggerSearch"
            class="w-full px-2 py-1 text-xs rounded-md bg-secondary/50 border border-border focus:outline-none focus:border-primary font-mono"
          />
          <span class="text-muted-foreground">–</span>
          <input
            type="number"
            placeholder="Max"
            v-model.number="stockStore.filters.price_max"
            @change="triggerSearch"
            class="w-full px-2 py-1 text-xs rounded-md bg-secondary/50 border border-border focus:outline-none focus:border-primary font-mono"
          />
        </div>
      </div>

      <!-- CPU & RAM -->
      <div class="grid grid-cols-2 gap-2">
        <div class="space-y-1">
          <label class="text-[11px] text-muted-foreground">CPU (≥ 核)</label>
          <input
            type="number"
            placeholder="如 1"
            v-model.number="stockStore.filters.cpu_min"
            @change="triggerSearch"
            class="w-full px-2 py-1 text-xs rounded-md bg-secondary/50 border border-border focus:outline-none focus:border-primary font-mono"
          />
        </div>
        <div class="space-y-1">
          <label class="text-[11px] text-muted-foreground">内存 (≥ MB)</label>
          <input
            type="number"
            placeholder="如 1024"
            v-model.number="stockStore.filters.ram_min"
            @change="triggerSearch"
            class="w-full px-2 py-1 text-xs rounded-md bg-secondary/50 border border-border focus:outline-none focus:border-primary font-mono"
          />
        </div>
      </div>

      <!-- Disk & Traffic -->
      <div class="grid grid-cols-2 gap-2">
        <div class="space-y-1">
          <label class="text-[11px] text-muted-foreground">硬盘 (≥ GB)</label>
          <input
            type="number"
            placeholder="如 20"
            v-model.number="stockStore.filters.disk_min"
            @change="triggerSearch"
            class="w-full px-2 py-1 text-xs rounded-md bg-secondary/50 border border-border focus:outline-none focus:border-primary font-mono"
          />
        </div>
        <div class="space-y-1">
          <label class="text-[11px] text-muted-foreground">月流量 (≥ GB)</label>
          <input
            type="number"
            placeholder="如 1000"
            v-model.number="stockStore.filters.traffic_min"
            @change="triggerSearch"
            class="w-full px-2 py-1 text-xs rounded-md bg-secondary/50 border border-border focus:outline-none focus:border-primary font-mono"
          />
        </div>
      </div>
    </div>

    <!-- Facet Group: 计费周期 (Cycle) -->
    <div class="space-y-2 pt-2 border-t border-border/60">
      <div class="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
        计费周期
      </div>
      <div class="flex flex-wrap gap-1">
        <button
          v-for="item in stockStore.facets.cycle"
          :key="item.value"
          @click="toggleItem(stockStore.filters.cycles, item.value)"
          class="px-2 py-0.8 rounded-md text-xs border transition-all flex items-center gap-1"
          :class="stockStore.filters.cycles.includes(item.value) ? 'bg-primary text-primary-foreground border-primary font-medium' : 'bg-secondary/60 hover:bg-secondary text-muted-foreground border-transparent'"
        >
          <span>{{ translateCycle(item.value) }}</span>
          <span class="text-[10px] opacity-70 font-mono">{{ item.count }}</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { useStockStore } from '@/stores/stock'
import { SlidersHorizontal, RotateCcw, Bell } from 'lucide-vue-next'

const stockStore = useStockStore()

function onStockToggle(e) {
  stockStore.filters.stock = e.target.checked ? 'in_stock' : ''
  triggerSearch()
}

function toggleItem(arr, val) {
  const idx = arr.indexOf(val)
  if (idx >= 0) {
    arr.splice(idx, 1)
  } else {
    arr.push(val)
  }
  triggerSearch()
}

function triggerSearch() {
  stockStore.fetchProducts()
}

function translateCycle(c) {
  const map = {
    monthly: '月付',
    quarterly: '季付',
    semiannually: '半年付',
    annually: '年付',
    biennially: '两年付',
    triennially: '三年付',
  }
  return map[c] || c
}
</script>
