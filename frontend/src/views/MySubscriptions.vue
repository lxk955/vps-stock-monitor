<template>
  <div class="min-h-screen bg-background text-foreground flex flex-col font-sans">
    <Navbar />

    <main class="max-w-3xl w-full mx-auto px-4 py-8 flex-1 space-y-6">
      <!-- Header -->
      <div class="p-6 rounded-2xl bg-card border border-border/80 shadow-xs space-y-2">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <BellRing class="w-5 h-5" />
          </div>
          <div>
            <h1 class="font-extrabold text-lg sm:text-xl text-foreground">我的 VPS 关注与降价通知</h1>
            <p class="text-xs text-muted-foreground">管理当前邮箱绑定的所有产品监控与通知策略</p>
          </div>
        </div>
      </div>

      <!-- Loading / Empty / List -->
      <div v-if="loading" class="py-16 text-center text-xs text-muted-foreground space-y-2">
        <Loader2 class="w-6 h-6 animate-spin mx-auto text-primary" />
        <p>正在读取您的订阅关注记录...</p>
      </div>

      <div v-else-if="subscriptions.length === 0" class="p-12 text-center bg-card rounded-2xl border border-border/60 space-y-3">
        <BellOff class="w-10 h-10 mx-auto text-muted-foreground opacity-40" />
        <p class="text-sm font-bold text-foreground">未找到任何有效的关注订阅</p>
        <p class="text-xs text-muted-foreground">您的关注可能已被取消，或该访问链接已失效。</p>
        <router-link
          to="/"
          class="inline-block px-5 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity"
        >
          返回 VPS 监控首页
        </router-link>
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="sub in subscriptions"
          :key="sub.id"
          class="p-4 rounded-xl bg-card border border-border/80 hover:border-primary/40 transition-all shadow-xs space-y-3"
        >
          <div class="flex items-start justify-between gap-3">
            <div>
              <span class="px-2 py-0.5 rounded bg-secondary text-foreground text-[10px] font-semibold border border-border/40 mr-2">
                {{ sub.provider }}
              </span>
              <span class="font-bold text-sm text-foreground">{{ sub.product_name }}</span>
            </div>

            <div class="text-right font-mono shrink-0">
              <span class="font-bold text-primary">${{ sub.current_price }}</span>
              <span class="text-[10px] text-muted-foreground"> {{ sub.currency }}</span>
            </div>
          </div>

          <div class="flex items-center justify-between pt-2 border-t border-border/60 text-xs">
            <div class="flex items-center gap-3 text-[11px]">
              <span :class="sub.notify_stock ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-muted-foreground line-through'">
                ⚡ 补货通知
              </span>
              <span :class="sub.notify_price_drop ? 'text-amber-600 dark:text-amber-400 font-medium' : 'text-muted-foreground line-through'">
                📉 降价通知
              </span>
              <span v-if="sub.target_price" class="text-primary font-mono font-medium">
                (期望价: ≤ ${{ sub.target_price }})
              </span>
            </div>

            <button
              @click="cancelSub(sub)"
              class="px-3 py-1 rounded-lg text-destructive hover:bg-destructive/10 border border-destructive/20 text-xs font-semibold transition-colors"
            >
              取消关注
            </button>
          </div>
        </div>
      </div>
    </main>

    <Toast ref="toastRef" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '@/api'
import Navbar from '@/components/Navbar.vue'
import Toast from '@/components/Toast.vue'
import { BellRing, BellOff, Loader2 } from 'lucide-vue-next'

const route = useRoute()
const subscriptions = ref([])
const loading = ref(true)
const toastRef = ref(null)

onMounted(async () => {
  const token = route.query.token
  const email = route.query.email

  if (!token && !email) {
    loading.value = false
    return
  }

  try {
    const list = await api.getMySubscriptions({ token, email })
    subscriptions.value = list
  } catch (err) {
    toastRef.value?.show(err.message || '加载订阅失败', 'error')
  } finally {
    loading.value = false
  }
})

async function cancelSub(sub) {
  try {
    await api.unsubscribe(sub.id, sub.unsubscribe_token)
    subscriptions.value = subscriptions.value.filter(s => s.id !== sub.id)
    toastRef.value?.show('已成功取消该产品的关注', 'success')
  } catch (err) {
    toastRef.value?.show(err.message || '操作失败', 'error')
  }
}
</script>
