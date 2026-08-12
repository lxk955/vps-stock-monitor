<template>
  <div class="rounded-xl border border-border/80 bg-card p-4 shadow-xs hover:shadow-md transition-all flex flex-col justify-between space-y-3 group hover:border-primary/40 relative">
    <!-- Top Row: Name, Group & Badges -->
    <div>
      <div class="flex items-start justify-between gap-2 mb-1.5">
        <div>
          <span class="px-1.5 py-0.5 rounded bg-secondary text-foreground text-[10px] font-semibold mr-1.5 border border-border/40">
            {{ product.provider }}
          </span>
          <span v-if="product.recommended" class="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-bold text-[10px] border border-amber-500/20 mr-1">
            ⭐ 推荐
          </span>
          <span v-if="product.previous_price && product.price < product.previous_price" class="px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold text-[10px] border border-rose-500/20">
            📉 降价
          </span>
        </div>

        <!-- Stock Status Badge -->
        <span
          v-if="product.status === 'in_stock'"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-[10px] font-bold shrink-0"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
          <span>{{ product.stock_qty ? `剩 ${product.stock_qty}` : '有货' }}</span>
        </span>
        <span
          v-else
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-500 border border-slate-500/20 text-[10px] font-medium shrink-0"
        >
          <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
          <span>缺货</span>
        </span>
      </div>

      <!-- Title -->
      <h3
        @click="emit('open-history', product)"
        class="font-bold text-sm text-foreground hover:text-primary transition-colors cursor-pointer leading-snug line-clamp-2"
      >
        {{ product.name }}
      </h3>
      <p v-if="product.group" class="text-[11px] text-muted-foreground mt-0.5 truncate">
        {{ product.group }}
      </p>

      <!-- Region & Line Pills -->
      <div class="flex flex-wrap gap-1 mt-2.5">
        <span
          v-for="r in product.regions"
          :key="r"
          class="px-1.5 py-0.5 rounded bg-secondary text-muted-foreground text-[10px] font-medium"
        >
          {{ r }}
        </span>
        <span
          v-for="l in product.lines"
          :key="l"
          class="px-1.5 py-0.5 rounded bg-primary/10 text-primary text-[10px] font-semibold border border-primary/20"
        >
          {{ l }}
        </span>
      </div>
    </div>

    <!-- Middle: Specs Box -->
    <div class="rounded-lg bg-secondary/40 p-2.5 text-xs text-muted-foreground grid grid-cols-2 gap-1.5 font-mono">
      <div>🖥️ <span class="text-foreground font-semibold">{{ product.cpu || '—' }}</span></div>
      <div>🧠 <span class="text-foreground font-semibold">{{ product.ram || '—' }}</span></div>
      <div>💾 <span>{{ product.disk || '—' }}</span></div>
      <div>🌐 <span>{{ product.transfer || '—' }}</span></div>
      <div class="col-span-2">🚀 <span>{{ product.port_speed || '—' }}</span></div>
    </div>

    <!-- Bottom: Price, Clicks & Actions -->
    <div class="pt-2 border-t border-border/60 flex items-center justify-between gap-2">
      <!-- Price -->
      <div>
        <div class="text-base font-extrabold text-foreground font-mono leading-tight">
          <span class="text-xs font-semibold text-muted-foreground mr-0.5">{{ getCurrencySymbol(product.currency) }}</span>
          <span>{{ product.price }}</span>
          <span class="text-[10px] font-normal text-muted-foreground ml-1">{{ product.currency }}</span>
        </div>
        <div class="text-[10px] text-muted-foreground">
          <span v-if="product.original_price && product.original_price > product.price" class="line-through mr-1 opacity-70">
            {{ getCurrencySymbol(product.currency) }}{{ product.original_price }}
          </span>
          <span>/ {{ translateCycle(product.price_cycle) }}</span>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-1.5">
        <!-- Watch Button -->
        <button
          @click="emit('open-watch', product)"
          class="p-2 rounded-lg border transition-all"
          :class="watchlistStore.isWatched(product.id) ? 'bg-primary/15 text-primary border-primary/40' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
          :title="watchlistStore.isWatched(product.id) ? '已关注 (点击修改)' : '加关注：有货/降价邮件通知'"
        >
          <Bell class="w-3.5 h-3.5" :class="{ 'fill-primary text-primary': watchlistStore.isWatched(product.id) }" />
        </button>

        <!-- Buy Button -->
        <a
          v-if="product.affiliate_url"
          :href="product.affiliate_url"
          target="_blank"
          @click="onBuyClick(product)"
          class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold shadow-xs transition-all"
          :class="product.status === 'in_stock' ? 'bg-primary text-primary-foreground hover:opacity-90' : 'bg-muted text-muted-foreground hover:bg-muted/80'"
        >
          <span>购买</span>
          <ExternalLink class="w-3 h-3" />
        </a>
        <button
          v-else
          disabled
          class="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-muted text-muted-foreground opacity-60 cursor-not-allowed"
        >
          <span>直达</span>
          <ExternalLink class="w-3 h-3" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useWatchlistStore } from '@/stores/watchlist'
import { api } from '@/api'
import { ExternalLink, Bell } from 'lucide-vue-next'

const props = defineProps({
  product: {
    type: Object,
    required: true,
  },
})

const emit = defineEmits(['open-watch', 'open-history'])
const watchlistStore = useWatchlistStore()

function onBuyClick(product) {
  api.recordClick(product.id).catch(() => {})
}

function getCurrencySymbol(curr) {
  const map = {
    USD: '$',
    EUR: '€',
    CNY: '¥',
    GBP: '£',
    HKD: 'HK$',
    CAD: 'CA$',
  }
  return map[curr] || '$'
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
