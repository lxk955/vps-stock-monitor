<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
  >
    <div class="relative w-full max-w-sm bg-card border border-border rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Modal Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border/80 bg-secondary/30">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-sky-500/10 text-sky-500 flex items-center justify-center">
            <Send class="w-4 h-4" />
          </div>
          <div>
            <h3 class="font-bold text-sm text-foreground">{{ type === 'channel' ? '加入 VPS 实时推送频道' : '加入 VPS 玩家交流群' }}</h3>
            <p class="text-[11px] text-muted-foreground">获取第一手补货通知与技术讨论</p>
          </div>
        </div>

        <button @click="close" class="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-5 text-center space-y-4 text-xs">
        <div class="p-4 rounded-xl bg-secondary/40 border border-border/60 space-y-2">
          <div class="text-3xl">✈️</div>
          <div class="font-bold text-sm text-foreground">
            {{ type === 'channel' ? 'Telegram VPS 补货频道' : 'Telegram VPS 交流互助群' }}
          </div>
          <p class="text-muted-foreground text-[11px]">
            {{ type === 'channel' ? '频道 24 小时自动播报最新补货、特惠促销与闪购动态。' : '与数千位 VPS 极客在线交流线路测速、建站调优与神机转让。' }}
          </p>
        </div>

        <a
          :href="type === 'channel' ? 'https://t.me/vps_stock_channel' : 'https://t.me/vps_stock_group'"
          target="_blank"
          class="block w-full py-2.5 px-4 rounded-xl bg-sky-500 hover:bg-sky-600 text-white font-bold transition-colors shadow-xs"
        >
          👉 立即点击前往加入
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'
import { Send, X } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
  type: String, // 'group' | 'channel'
})

const emit = defineEmits(['update:visible'])

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
</script>
