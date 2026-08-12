<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 p-4 bg-black/50 backdrop-blur-xs"
  >
    <div class="relative w-full max-w-2xl bg-card border border-border rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[80vh]">
      <!-- Search Input Bar -->
      <div class="flex items-center px-4 py-3.5 border-b border-border/70 bg-secondary/20 shrink-0 gap-3">
        <Search class="w-5 h-5 text-muted-foreground shrink-0" />
        <input
          ref="searchInput"
          type="text"
          v-model="query"
          @input="onSearch"
          placeholder="搜索 VPS 厂商、机房位置、线路（如 CN2 GIA、9929）、CPU、内存..."
          class="w-full bg-transparent text-sm text-foreground focus:outline-none placeholder:text-muted-foreground"
        />
        <kbd class="px-2 py-0.5 text-[10px] font-mono bg-secondary rounded border border-border text-muted-foreground">ESC</kbd>
        <button @click="close" class="p-1 rounded-md hover:bg-secondary text-muted-foreground">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Results list -->
      <div class="p-3 overflow-y-auto divide-y divide-border/40 flex-1">
        <div v-if="loading" class="py-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
          <Loader2 class="w-4 h-4 animate-spin text-primary" />
          <span>正在实时搜索中...</span>
        </div>

        <div v-else-if="results.length === 0" class="py-8 text-center text-xs text-muted-foreground">
          {{ query ? '未找到匹配的 VPS 机型' : '输入关键词即可快速查找机型' }}
        </div>

        <div
          v-for="item in results"
          :key="item.id"
          class="p-3 hover:bg-secondary/40 rounded-xl transition-colors cursor-pointer flex items-center justify-between gap-3 text-xs"
        >
          <div class="space-y-1">
            <div class="flex items-center gap-1.5 flex-wrap">
              <span class="px-1.5 py-0.2 rounded bg-secondary text-foreground text-[10px] font-semibold border border-border/50">
                {{ item.provider }}
              </span>
              <span class="font-bold text-foreground">{{ item.name }}</span>
              <span
                v-if="item.status === 'in_stock'"
                class="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-600 font-bold text-[10px]"
              >
                有货
              </span>
              <span v-else class="px-1.5 py-0.2 rounded bg-slate-500/10 text-slate-500 text-[10px]">
                缺货
              </span>
            </div>

            <div class="text-[11px] text-muted-foreground font-mono">
              {{ item.cpu }} · {{ item.ram }} · {{ item.disk }} · {{ item.transfer }} · {{ item.port_speed }}
            </div>
          </div>

          <div class="flex items-center gap-2 shrink-0">
            <div class="text-right font-mono">
              <div class="font-bold text-sm text-foreground">
                {{ getCurrencySymbol(item.currency) }}{{ item.price }}
                <span class="text-[10px] font-normal text-muted-foreground">{{ item.currency }}</span>
              </div>
              <div class="text-[10px] text-muted-foreground">/{{ item.price_cycle }}</div>
            </div>

            <button
              @click.stop="openWatch(item)"
              class="p-1.5 rounded-lg border border-border hover:bg-secondary text-muted-foreground hover:text-primary transition-colors"
              title="加关注"
            >
              <Bell class="w-3.5 h-3.5" />
            </button>

            <a
              v-if="item.affiliate_url"
              :href="item.affiliate_url"
              target="_blank"
              class="p-1.5 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90 transition-opacity"
              title="前往官网购买"
            >
              <ExternalLink class="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { api } from '@/api'
import { Search, Bell, ExternalLink, X, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
})

const emit = defineEmits(['update:visible', 'open-watch'])

const query = ref('')
const results = ref([])
const loading = ref(false)
const searchInput = ref(null)

let searchTimer = null
let currentAbortController = null

function getCurrencySymbol(curr) {
  const map = { USD: '$', EUR: '€', CNY: '¥', GBP: '£', HKD: 'HK$', CAD: 'CA$' }
  return map[curr] || '$'
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => searchInput.value?.focus())
    if (!query.value) {
      loadInitial()
    }
  }
})

function close() {
  if (currentAbortController) currentAbortController.abort()
  emit('update:visible', false)
}

function handleKeydown(e) {
  if (props.visible && e.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  if (searchTimer) clearTimeout(searchTimer)
  if (currentAbortController) currentAbortController.abort()
})

async function loadInitial() {
  loading.value = true
  if (currentAbortController) currentAbortController.abort()
  currentAbortController = new AbortController()

  try {
    const res = await api.getProducts({ size: 10, sort: 'value' }, { signal: currentAbortController.signal })
    results.value = res.products
  } catch (err) {
    if (err.name !== 'AbortError') console.warn(err)
  } finally {
    loading.value = false
  }
}

function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    loading.value = true
    if (currentAbortController) currentAbortController.abort()
    currentAbortController = new AbortController()

    try {
      const res = await api.getProducts({ q: query.value, size: 20 }, { signal: currentAbortController.signal })
      results.value = res.products
    } catch (err) {
      if (err.name !== 'AbortError') console.warn(err)
    } finally {
      loading.value = false
    }
  }, 200)
}

function openWatch(item) {
  close()
  emit('open-watch', item)
}
</script>
