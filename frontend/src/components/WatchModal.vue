<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
  >
    <div class="relative w-full max-w-md bg-card border border-border rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Modal Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border/80 bg-secondary/30">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
            <Bell class="w-4 h-4" />
          </div>
          <div>
            <h3 class="font-bold text-sm text-foreground">关注产品与邮件提醒</h3>
            <p class="text-[11px] text-muted-foreground">当产品补货或降价时，第一时间邮件通知您</p>
          </div>
        </div>

        <button @click="close" class="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-5 space-y-4">
        <!-- Product Snapshot -->
        <div v-if="product" class="p-3 rounded-xl bg-secondary/40 border border-border/60 text-xs space-y-1">
          <div class="flex items-center justify-between">
            <span class="font-bold text-foreground truncate max-w-[260px]">{{ product.name }}</span>
            <span class="font-bold text-primary font-mono">{{ getCurrencySymbol(product.currency) }}{{ product.price }} {{ product.currency }}</span>
          </div>
          <div class="text-muted-foreground font-mono text-[11px]">
            {{ product.provider }} · {{ product.cpu }} · {{ product.ram }} · {{ product.disk }}
          </div>
        </div>

        <!-- Form -->
        <form @submit.prevent="submitWatch" class="space-y-4 text-xs">
          <!-- Email Input -->
          <div class="space-y-1">
            <label class="font-semibold text-foreground flex items-center justify-between">
              <span>通知接收邮箱 <span class="text-rose-500">*</span></span>
              <span class="text-[10px] text-muted-foreground">无需密码，自动关联</span>
            </label>
            <div class="relative">
              <Mail class="w-4 h-4 absolute left-3 top-2.5 text-muted-foreground" />
              <input
                type="email"
                required
                v-model="form.email"
                placeholder="your-email@example.com"
                class="w-full pl-9 pr-3 py-2 text-xs rounded-lg bg-background border border-border focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono"
              />
            </div>
          </div>

          <!-- Notification Toggles -->
          <div class="space-y-2.5 pt-1">
            <label class="flex items-start gap-2.5 p-2.5 rounded-lg border border-border/60 hover:bg-secondary/30 cursor-pointer transition-colors">
              <input
                type="checkbox"
                v-model="form.notifyStock"
                class="mt-0.5 rounded border-border text-primary focus:ring-primary"
              />
              <div class="space-y-0.5">
                <div class="font-semibold text-foreground flex items-center gap-1">
                  <span>⚡ 补货上架提醒</span>
                  <span class="text-[10px] px-1 py-0.2 rounded bg-emerald-500/10 text-emerald-600 font-bold">Back in Stock</span>
                </div>
                <div class="text-[11px] text-muted-foreground">当监控到该机型从缺货变更为有货时立即发送邮件通知</div>
              </div>
            </label>

            <label class="flex items-start gap-2.5 p-2.5 rounded-lg border border-border/60 hover:bg-secondary/30 cursor-pointer transition-colors">
              <input
                type="checkbox"
                v-model="form.notifyPriceDrop"
                class="mt-0.5 rounded border-border text-primary focus:ring-primary"
              />
              <div class="space-y-0.5">
                <div class="font-semibold text-foreground flex items-center gap-1">
                  <span>📉 降价优惠提醒</span>
                  <span class="text-[10px] px-1 py-0.2 rounded bg-amber-500/10 text-amber-600 font-bold">Price Drop</span>
                </div>
                <div class="text-[11px] text-muted-foreground">当产品官方价格调低或触发促销折扣时发送通知</div>
              </div>
            </label>
          </div>

          <!-- Optional: Target Price Threshold -->
          <div v-if="form.notifyPriceDrop" class="space-y-1 pt-1">
            <label class="font-semibold text-foreground flex items-center justify-between">
              <span>期望目标价格 (可选)</span>
              <span class="text-[10px] text-muted-foreground">低于该价格才通知</span>
            </label>
            <div class="relative">
              <span class="absolute left-3 top-2 text-muted-foreground font-mono">{{ getCurrencySymbol(product?.currency) }}</span>
              <input
                type="number"
                step="0.01"
                v-model="form.targetPrice"
                :placeholder="`当前价格: ${product?.price || '0.00'}`"
                class="w-full pl-7 pr-3 py-1.5 text-xs rounded-lg bg-background border border-border focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary font-mono"
              />
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex items-center gap-2 pt-2">
            <button
              type="submit"
              :disabled="submitting || (!form.notifyStock && !form.notifyPriceDrop)"
              class="flex-1 py-2 px-4 rounded-lg bg-primary text-primary-foreground font-bold hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2 shadow-xs"
            >
              <Loader2 v-if="submitting" class="w-4 h-4 animate-spin" />
              <span>{{ isAlreadyWatched ? '更新关注提醒' : '立即开启关注' }}</span>
            </button>

            <button
              v-if="isAlreadyWatched"
              type="button"
              @click="cancelWatch"
              :disabled="submitting"
              class="py-2 px-3 rounded-lg border border-destructive/30 text-destructive hover:bg-destructive/10 transition-colors font-medium"
              title="取消关注此产品"
            >
              取消关注
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useWatchlistStore } from '@/stores/watchlist'
import { Bell, X, Mail, Loader2 } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
  product: Object,
})

const emit = defineEmits(['update:visible', 'success', 'error'])
const watchlistStore = useWatchlistStore()

const submitting = ref(false)
const form = ref({
  email: '',
  notifyStock: true,
  notifyPriceDrop: true,
  targetPrice: '',
})

function getCurrencySymbol(curr) {
  const map = { USD: '$', EUR: '€', CNY: '¥', GBP: '£', HKD: 'HK$', CAD: 'CA$' }
  return map[curr] || '$'
}

const isAlreadyWatched = computed(() => {
  return props.product ? watchlistStore.isWatched(props.product.id) : false
})

watch(() => props.product, (newProd) => {
  if (newProd) {
    const existing = watchlistStore.getWatchInfo(newProd.id)
    if (existing) {
      form.value = {
        email: existing.email || watchlistStore.userEmail || '',
        notifyStock: existing.notifyStock !== false,
        notifyPriceDrop: existing.notifyPriceDrop !== false,
        targetPrice: existing.targetPrice || '',
      }
    } else {
      form.value = {
        email: watchlistStore.userEmail || '',
        notifyStock: true,
        notifyPriceDrop: true,
        targetPrice: '',
      }
    }
  }
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

async function submitWatch() {
  if (!props.product) return
  submitting.value = true
  try {
    const res = await watchlistStore.addWatch({
      productId: props.product.id,
      email: form.value.email,
      notifyStock: form.value.notifyStock,
      notifyPriceDrop: form.value.notifyPriceDrop,
      targetPrice: form.value.targetPrice,
    })
    emit('success', res.message || '关注成功！')
    close()
  } catch (err) {
    emit('error', err.message || '关注失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

async function cancelWatch() {
  if (!props.product) return
  submitting.value = true
  try {
    await watchlistStore.removeWatch(props.product.id)
    emit('success', '已成功取消对该产品的关注')
    close()
  } catch (err) {
    emit('error', err.message || '取消关注失败')
  } finally {
    submitting.value = false
  }
}
</script>
