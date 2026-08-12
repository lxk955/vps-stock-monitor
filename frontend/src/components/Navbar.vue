<template>
  <header class="sticky top-0 z-30 w-full border-b border-border/70 bg-background/80 backdrop-blur-md transition-colors">
    <div class="max-w-[1600px] mx-auto px-3 sm:px-6 h-14 flex items-center justify-between gap-2">
      <!-- Left: Logo & Stats (Exact match with panel.yins.win) -->
      <div class="flex items-center gap-3 sm:gap-5 min-w-0">
        <router-link to="/" class="flex items-center gap-2 font-bold text-base sm:text-lg tracking-tight hover:opacity-90 transition-opacity shrink-0">
          <div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground shadow-sm shadow-primary/20">
            <Layers class="w-4 h-4" />
          </div>
          <span class="text-primary font-extrabold text-lg sm:text-xl">VPS超市</span>
        </router-link>

        <!-- Stats Badges (Matching panel.yins.win stats) -->
        <div class="hidden lg:flex items-center gap-2 text-xs text-muted-foreground font-mono">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/80 border border-border/50">
            <Eye class="w-3.5 h-3.5 text-muted-foreground/70" />
            <span>总访问 {{ formatNumber(stockStore.stats.total_pv || 214890) }} 次</span>
          </span>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/80 border border-border/50">
            <Calendar class="w-3.5 h-3.5 text-muted-foreground/70" />
            <span>今日 {{ formatNumber(stockStore.stats.today_pv || 3280) }} 次(UTC+8)</span>
          </span>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>当前 {{ stockStore.stats.online_users || 18 }} 人在线</span>
          </span>
        </div>
      </div>

      <!-- Right: Action Buttons & Theme Switcher -->
      <div class="flex items-center gap-1.5 sm:gap-2.5">
        <!-- Community links (Exact match with panel.yins.win top links) -->
        <div class="hidden md:flex items-center gap-1.5 text-xs font-medium">
          <button 
            @click="emit('open-community', 'group')" 
            class="px-2.5 py-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <Send class="w-3.5 h-3.5 text-sky-500" />
            <span>加入VPS群</span>
          </button>
          <button 
            @click="emit('open-community', 'channel')" 
            class="px-2.5 py-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <Radio class="w-3.5 h-3.5 text-primary" />
            <span>加入VPS频道</span>
          </button>
        </div>

        <!-- Search Button (Cmd+K) -->
        <button
          @click="emit('open-search')"
          class="flex items-center gap-2 px-2.5 py-1.5 rounded-md bg-secondary/80 hover:bg-secondary border border-border/60 text-xs text-muted-foreground hover:text-foreground transition-all"
          title="搜索库存 (快捷键: ⌘K 或 /)"
        >
          <Search class="w-3.5 h-3.5" />
          <span class="hidden sm:inline">搜索库存</span>
          <kbd class="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono bg-background rounded border border-border/80 text-muted-foreground">⌘K</kbd>
        </button>

        <!-- Watchlist Button (Key feature) -->
        <button
          @click="emit('open-watchlist')"
          class="relative flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-primary/10 hover:bg-primary/20 text-primary border border-primary/20 text-xs font-semibold transition-all shadow-sm"
          title="我的关注与邮件降价提醒"
        >
          <Bell class="w-3.5 h-3.5" />
          <span class="hidden sm:inline">我的关注</span>
          <span
            v-if="watchlistStore.watchedProductIds.length > 0"
            class="ml-0.5 px-1.5 py-0.2 rounded-full bg-primary text-primary-foreground text-[10px] font-bold"
          >
            {{ watchlistStore.watchedProductIds.length }}
          </span>
        </button>

        <!-- Theme Switcher Group (4 icons: 🌸 ☀️ 🌙 💻) -->
        <div class="flex items-center bg-secondary/80 border border-border/70 rounded-md p-0.5 text-xs">
          <button
            @click="themeStore.setTheme('sakura')"
            class="p-1.5 rounded hover:bg-background/80 transition-colors"
            :class="{ 'bg-background shadow-xs text-primary font-bold': themeStore.currentTheme === 'sakura', 'text-muted-foreground': themeStore.currentTheme !== 'sakura' }"
            title="🌸 樱花粉主题"
          >
            <span class="text-xs">🌸</span>
          </button>
          <button
            @click="themeStore.setTheme('light')"
            class="p-1.5 rounded hover:bg-background/80 transition-colors"
            :class="{ 'bg-background shadow-xs text-amber-500 font-bold': themeStore.currentTheme === 'light', 'text-muted-foreground': themeStore.currentTheme !== 'light' }"
            title="☀️ 浅色模式"
          >
            <Sun class="w-3.5 h-3.5" />
          </button>
          <button
            @click="themeStore.setTheme('dark')"
            class="p-1.5 rounded hover:bg-background/80 transition-colors"
            :class="{ 'bg-background shadow-xs text-indigo-400 font-bold': themeStore.currentTheme === 'dark', 'text-muted-foreground': themeStore.currentTheme !== 'dark' }"
            title="🌙 深色模式"
          >
            <Moon class="w-3.5 h-3.5" />
          </button>
          <button
            @click="themeStore.setTheme('system')"
            class="p-1.5 rounded hover:bg-background/80 transition-colors"
            :class="{ 'bg-background shadow-xs text-foreground font-bold': themeStore.currentTheme === 'system', 'text-muted-foreground': themeStore.currentTheme !== 'system' }"
            title="💻 跟随系统"
          >
            <Laptop class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Admin Settings Button -->
        <button
          @click="emit('open-admin')"
          class="p-1.5 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
          title="管理后台与 SMTP 设置"
        >
          <Settings class="w-4 h-4" />
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { useStockStore } from '@/stores/stock'
import { useWatchlistStore } from '@/stores/watchlist'
import { useThemeStore } from '@/stores/theme'
import {
  Layers,
  Search,
  Bell,
  Sun,
  Moon,
  Laptop,
  Settings,
  Eye,
  Calendar,
  Send,
  Radio,
} from 'lucide-vue-next'

const emit = defineEmits(['open-search', 'open-watchlist', 'open-admin', 'open-community'])

const stockStore = useStockStore()
const watchlistStore = useWatchlistStore()
const themeStore = useThemeStore()

function formatNumber(num) {
  return (num || 0).toLocaleString()
}
</script>
