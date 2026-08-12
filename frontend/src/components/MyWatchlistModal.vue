<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
  >
    <div class="relative w-full max-w-2xl bg-card border border-border rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200 max-h-[90vh] flex flex-col">
      <!-- Modal Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border/80 bg-secondary/30 shrink-0">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
            <BellRing class="w-4 h-4" />
          </div>
          <div>
            <h3 class="font-bold text-sm text-foreground">我的关注管理中心</h3>
            <p class="text-[11px] text-muted-foreground">管理您关注的 VPS 产品、接收邮箱与通知策略</p>
          </div>
        </div>

        <button @click="close" class="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Tabs Navigation -->
      <div class="flex items-center border-b border-border/60 px-5 bg-secondary/10 shrink-0">
        <button
          @click="activeTab = 'list'"
          class="py-2.5 px-3 text-xs font-semibold border-b-2 transition-all"
          :class="activeTab === 'list' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'"
        >
          关注列表 ({{ watchedList.length }})
        </button>
        <button
          @click="activeTab = 'sync'"
          class="py-2.5 px-3 text-xs font-semibold border-b-2 transition-all flex items-center gap-1"
          :class="activeTab === 'sync' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'"
        >
          <RefreshCw class="w-3 h-3" />
          <span>跨设备同步 / 找回</span>
        </button>
      </div>

      <!-- Modal Body (Scrollable) -->
      <div class="p-5 overflow-y-auto space-y-4 flex-1">
        <!-- TAB 1: List -->
        <div v-if="activeTab === 'list'" class="space-y-3">
          <div v-if="watchedList.length === 0" class="py-12 text-center text-muted-foreground space-y-2">
            <BellOff class="w-8 h-8 mx-auto opacity-40 text-muted-foreground" />
            <p class="text-xs font-medium">您暂未关注任何 VPS 产品</p>
            <p class="text-[11px] opacity-70">在列表中点击【加关注】按钮，即可开启有货和降价邮件提醒。</p>
          </div>

          <div
            v-for="item in watchedList"
            :key="item.id || item.productId"
            class="p-3.5 rounded-xl border border-border/70 bg-card hover:bg-secondary/20 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
          >
            <!-- Left Info -->
            <div class="space-y-1">
              <div class="flex items-center gap-1.5 flex-wrap">
                <span class="font-bold text-foreground">{{ item.product_name || getLocalProductName(item.productId) }}</span>
                <span
                  v-if="getProductStatus(item.productId) === 'in_stock'"
                  class="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-600 font-bold text-[10px]"
                >
                  🟢 有货
                </span>
                <span v-else class="px-1.5 py-0.2 rounded bg-slate-500/10 text-slate-500 text-[10px]">
                  ⚪ 缺货
                </span>
              </div>

              <div class="text-[11px] text-muted-foreground flex items-center gap-2 flex-wrap">
                <span>📧 {{ item.email }}</span>
                <span>·</span>
                <span class="text-emerald-600 dark:text-emerald-400 font-medium">
                  {{ item.notify_stock !== false ? '⚡ 补货通知' : '' }}
                </span>
                <span class="text-amber-600 dark:text-amber-400 font-medium">
                  {{ item.notify_price_drop !== false ? '📉 降价通知' : '' }}
                </span>
                <span v-if="item.target_price" class="text-primary font-medium font-mono">
                  (≤ ${{ item.target_price }})
                </span>
              </div>
            </div>

            <!-- Right Actions -->
            <div class="flex items-center gap-2 shrink-0">
              <button
                @click="openEditWatch(item)"
                class="px-2.5 py-1 rounded-md bg-secondary hover:bg-secondary/80 text-foreground border border-border text-xs font-medium transition-colors"
              >
                修改
              </button>
              <button
                @click="deleteWatch(item)"
                class="px-2.5 py-1 rounded-md text-destructive hover:bg-destructive/10 border border-destructive/20 text-xs font-medium transition-colors"
              >
                取消关注
              </button>
            </div>
          </div>
        </div>

        <!-- TAB 2: Sync & Magic Link -->
        <div v-else-if="activeTab === 'sync'" class="space-y-4 text-xs">
          <div class="p-4 rounded-xl bg-secondary/30 border border-border space-y-3">
            <h4 class="font-bold text-foreground">跨设备同步关注列表</h4>
            <p class="text-muted-foreground text-[11px] leading-relaxed">
              如果您在另一台电脑或手机上订阅了关注，只需输入您订阅时填写的邮箱，即可一键同步拉取到当前设备，或向该邮箱发送专属免密管理链接。
            </p>

            <div class="flex gap-2">
              <input
                type="email"
                v-model="syncEmailInput"
                placeholder="输入您关注时填写的邮箱"
                class="flex-1 px-3 py-2 text-xs rounded-lg bg-background border border-border focus:outline-none focus:border-primary font-mono"
              />
              <button
                @click="performSync"
                :disabled="syncing || !syncEmailInput"
                class="px-4 py-2 bg-primary text-primary-foreground font-bold rounded-lg hover:opacity-90 disabled:opacity-50 transition-all flex items-center gap-1.5 shrink-0"
              >
                <Loader2 v-if="syncing" class="w-3.5 h-3.5 animate-spin" />
                <span>立即拉取同步</span>
              </button>
            </div>

            <div class="pt-2">
              <button
                @click="sendMagicLink"
                :disabled="sendingLink || !syncEmailInput"
                class="text-[11px] text-primary hover:underline flex items-center gap-1 disabled:opacity-50"
              >
                <Send class="w-3 h-3" />
                <span>发送专属免密管理链接到该邮箱 ↗</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { useStockStore } from '@/stores/stock'
import { api } from '@/api'
import { BellRing, BellOff, X, RefreshCw, Send, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
})

const emit = defineEmits(['update:visible', 'open-watch', 'success', 'error'])
const watchlistStore = useWatchlistStore()
const stockStore = useStockStore()

const activeTab = ref('list')
const syncEmailInput = ref(watchlistStore.userEmail || '')
const syncing = ref(false)
const sendingLink = ref(false)

const watchedList = computed(() => {
  if (watchlistStore.remoteSubscriptions.length > 0) {
    return watchlistStore.remoteSubscriptions
  }
  return watchlistStore.localWatchlist
})

function close() {
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
})

function getLocalProductName(productId) {
  const p = stockStore.products.find(item => item.id === productId)
  return p ? `${p.provider} - ${p.name}` : `产品 #${productId}`
}

function getProductStatus(productId) {
  const p = stockStore.products.find(item => item.id === productId)
  return p ? p.status : 'unknown'
}

function openEditWatch(item) {
  const prodId = item.product_id || item.productId
  const p = stockStore.products.find(x => x.id === prodId)
  if (p) {
    close()
    emit('open-watch', p)
  }
}

async function deleteWatch(item) {
  const prodId = item.product_id || item.productId
  try {
    await watchlistStore.removeWatch(prodId)
    emit('success', '已取消关注该产品')
  } catch (err) {
    emit('error', err.message || '操作失败')
  }
}

async function performSync() {
  if (!syncEmailInput.value) return
  syncing.value = true
  try {
    watchlistStore.userEmail = syncEmailInput.value
    await watchlistStore.syncRemote()
    activeTab.value = 'list'
    emit('success', '已成功同步关注列表！')
  } catch (err) {
    emit('error', '同步失败，请检查邮箱是否正确')
  } finally {
    syncing.value = false
  }
}

async function sendMagicLink() {
  if (!syncEmailInput.value) return
  sendingLink.value = true
  try {
    const res = await api.requestMagicLink(syncEmailInput.value)
    emit('success', res.message || '管理链接已发送至您的邮箱！')
  } catch (err) {
    emit('error', err.message || '邮件发送失败，请确保管理员配置了 SMTP')
  } finally {
    sendingLink.value = false
  }
}
</script>
