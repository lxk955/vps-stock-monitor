<template>
  <div class="overflow-x-auto rounded-xl border border-border/80 bg-card shadow-xs">
    <table class="w-full text-left text-xs border-collapse">
      <!-- Table Header -->
      <thead class="bg-secondary/60 border-b border-border text-muted-foreground font-semibold uppercase tracking-wider">
        <tr>
          <th class="py-3 px-3.5 whitespace-nowrap w-36">操作</th>
          <th class="py-3 px-3.5 min-w-[220px]">产品</th>
          <th class="py-3 px-3.5 whitespace-nowrap">厂商</th>
          <th class="py-3 px-3.5 whitespace-nowrap text-right">价格</th>
          <th class="py-3 px-3.5 min-w-[200px]">规格配置</th>
          <th class="py-3 px-3.5 min-w-[150px]">地区 / 线路</th>
          <th class="py-3 px-3.5 whitespace-nowrap text-center">状态</th>
        </tr>
      </thead>

      <!-- Table Body -->
      <tbody class="divide-y divide-border/60 font-normal">
        <tr
          v-for="product in products"
          :key="product.id"
          class="hover:bg-secondary/30 transition-colors group"
        >
          <!-- 1. Actions Column: Buy + Watch + Clicks -->
          <td class="py-3 px-3.5 whitespace-nowrap align-middle">
            <div class="flex items-center gap-1.5">
              <!-- Buy Link -->
              <a
                v-if="product.affiliate_url"
                :href="product.affiliate_url"
                target="_blank"
                @click="onBuyClick(product)"
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold shadow-xs transition-all"
                :class="product.status === 'in_stock' ? 'bg-primary text-primary-foreground hover:opacity-90' : 'bg-muted text-muted-foreground hover:bg-muted/80'"
              >
                <span>购买</span>
                <ExternalLink class="w-3 h-3" />
              </a>
              <button
                v-else
                disabled
                class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium bg-muted text-muted-foreground opacity-60 cursor-not-allowed"
              >
                <span>直达</span>
                <ExternalLink class="w-3 h-3" />
              </button>

              <!-- Watch Button (User's core feature) -->
              <button
                @click="emit('open-watch', product)"
                class="p-1 rounded-md border transition-all flex items-center gap-1 text-[11px] font-medium"
                :class="watchlistStore.isWatched(product.id) ? 'bg-primary/15 text-primary border-primary/30 font-bold' : 'bg-background hover:bg-secondary text-muted-foreground border-border'"
                :title="watchlistStore.isWatched(product.id) ? '已开启有货/降价提醒 (点击修改)' : '加关注：有货或降价时邮件通知'"
              >
                <Bell class="w-3 h-3" :class="{ 'fill-primary text-primary': watchlistStore.isWatched(product.id) }" />
                <span class="hidden sm:inline">{{ watchlistStore.isWatched(product.id) ? '已关注' : '关注' }}</span>
              </button>
            </div>

            <div class="text-[10px] text-muted-foreground font-mono mt-1 flex items-center gap-1">
              <span>🔥 {{ product.clicks || 0 }} 次</span>
            </div>
          </td>

          <!-- 2. Product Column: Name + Group + Badges -->
          <td class="py-3 px-3.5 align-middle">
            <div class="space-y-0.5">
              <div class="flex flex-wrap items-center gap-1.5">
                <span
                  @click="emit('open-history', product)"
                  class="font-bold text-foreground text-xs hover:text-primary cursor-pointer transition-colors"
                >
                  {{ product.name }}
                </span>

                <!-- Badges -->
                <span v-if="product.recommended" class="px-1.5 py-0.2 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-bold text-[10px] border border-amber-500/20">
                  ⭐ 推荐
                </span>

                <span v-if="product.previous_price && product.price < product.previous_price" class="px-1.5 py-0.2 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-bold text-[10px] border border-rose-500/20">
                  📉 降价
                </span>
              </div>

              <div v-if="product.group" class="text-[11px] text-muted-foreground">
                {{ product.group }}
              </div>
            </div>
          </td>

          <!-- 3. Provider Column -->
          <td class="py-3 px-3.5 whitespace-nowrap align-middle">
            <span class="px-2 py-0.8 rounded-md bg-secondary text-foreground text-[11px] font-medium border border-border/50">
              {{ product.provider }}
            </span>
          </td>

          <!-- 4. Price Column with clean currency display -->
          <td class="py-3 px-3.5 whitespace-nowrap text-right align-middle font-mono">
            <div class="flex flex-col items-end">
              <div class="text-sm font-extrabold text-foreground">
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
          </td>

          <!-- 5. Specs Column -->
          <td class="py-3 px-3.5 align-middle text-muted-foreground text-[11px]">
            <div class="flex flex-wrap items-center gap-1.5 leading-relaxed font-mono">
              <span class="text-foreground font-semibold">{{ product.cpu || '—' }}</span>
              <span class="text-border">·</span>
              <span class="text-foreground font-semibold">{{ product.ram || '—' }}</span>
              <span class="text-border">·</span>
              <span>{{ product.disk || '—' }}</span>
              <span class="text-border">·</span>
              <span>{{ product.transfer || '—' }}</span>
              <span class="text-border">·</span>
              <span>{{ product.port_speed || '—' }}</span>
            </div>
          </td>

          <!-- 6. Region / Line Column -->
          <td class="py-3 px-3.5 align-middle">
            <div class="flex flex-wrap items-center gap-1">
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
          </td>

          <!-- 7. Status Column -->
          <td class="py-3 px-3.5 whitespace-nowrap text-center align-middle">
            <span
              v-if="product.status === 'in_stock'"
              class="inline-flex items-center gap-1 px-2 py-0.8 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-[11px] font-bold"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>{{ product.stock_qty ? `剩 ${product.stock_qty} 件` : '有货' }}</span>
            </span>
            <span
              v-else
              class="inline-flex items-center gap-1 px-2 py-0.8 rounded-full bg-slate-500/10 text-slate-500 border border-slate-500/20 text-[11px] font-medium"
            >
              <span class="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
              <span>缺货</span>
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { useWatchlistStore } from '@/stores/watchlist'
import { api } from '@/api'
import { ExternalLink, Bell } from 'lucide-vue-next'

const props = defineProps({
  products: {
    type: Array,
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
