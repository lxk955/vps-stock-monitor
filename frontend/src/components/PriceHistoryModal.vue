<template>
  <div
    v-if="visible"
    @click.self="close"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
  >
    <div class="relative w-full max-w-xl bg-card border border-border rounded-2xl shadow-xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Modal Header -->
      <div class="flex items-center justify-between px-5 py-4 border-b border-border/80 bg-secondary/30">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center">
            <TrendingDown class="w-4 h-4" />
          </div>
          <div>
            <h3 class="font-bold text-sm text-foreground">价格与库存历史趋势</h3>
            <p class="text-[11px] text-muted-foreground">{{ product?.provider }} - {{ product?.name }}</p>
          </div>
        </div>

        <button @click="close" class="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-colors">
          <X class="w-4 h-4" />
        </button>
      </div>

      <!-- Modal Body -->
      <div class="p-5 space-y-4 text-xs">
        <!-- Canvas Chart -->
        <div class="p-4 rounded-xl bg-secondary/30 border border-border/60">
          <div class="flex items-center justify-between mb-2 text-xs font-semibold text-muted-foreground">
            <span>价格走势 ({{ product?.currency }})</span>
            <span class="font-mono text-primary font-bold text-sm">
              {{ getCurrencySymbol(product?.currency) }}{{ product?.price }}
            </span>
          </div>

          <canvas ref="chartCanvas" class="w-full h-44 rounded-lg bg-background/50"></canvas>
        </div>

        <!-- History Records Table -->
        <div class="space-y-2">
          <div class="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider">
            变更记录明细
          </div>
          <div class="max-h-48 overflow-y-auto space-y-1.5 pr-1">
            <div
              v-for="record in historyList"
              :key="record.id"
              class="p-2 rounded-lg bg-secondary/40 border border-border/50 flex items-center justify-between font-mono text-[11px]"
            >
              <div class="flex items-center gap-2">
                <span :class="record.status === 'in_stock' ? 'text-emerald-500 font-bold' : 'text-slate-400'">
                  {{ record.status === 'in_stock' ? '🟢 有货' : '⚪ 缺货' }}
                </span>
                <span class="text-muted-foreground">{{ formatDate(record.recorded_at) }}</span>
              </div>
              <div class="font-bold text-foreground">
                {{ getCurrencySymbol(record.currency) }}{{ record.price }} {{ record.currency }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { api } from '@/api'
import { TrendingDown, X } from 'lucide-vue-next'

const props = defineProps({
  visible: Boolean,
  product: Object,
})

const emit = defineEmits(['update:visible'])
const chartCanvas = ref(null)
const historyList = ref([])

function getCurrencySymbol(curr) {
  const map = { USD: '$', EUR: '€', CNY: '¥', GBP: '£', HKD: 'HK$', CAD: 'CA$' }
  return map[curr] || '$'
}

watch(() => props.visible, async (newVal) => {
  if (newVal && props.product) {
    try {
      const data = await api.getPriceHistory(props.product.id)
      historyList.value = data.length > 0 ? data : [
        {
          id: 1,
          price: props.product.price,
          currency: props.product.currency,
          status: props.product.status,
          recorded_at: props.product.created_at || new Date().toISOString(),
        },
      ]
      // Draw after modal CSS zoom animation completes for sharp rendering
      setTimeout(() => {
        drawChart()
      }, 220)
    } catch (err) {
      console.warn('Failed to load price history:', err)
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
  window.addEventListener('resize', drawChart)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
  window.removeEventListener('resize', drawChart)
})

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

function drawChart() {
  if (!chartCanvas.value) return
  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  const dpr = window.devicePixelRatio || 1

  const rect = canvas.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) return

  canvas.width = rect.width * dpr
  canvas.height = rect.height * dpr
  ctx.scale(dpr, dpr)

  const width = rect.width
  const height = rect.height
  ctx.clearRect(0, 0, width, height)

  const data = historyList.value.map(item => item.price)
  if (data.length === 1) data.unshift(data[0])

  const min = Math.min(...data) * 0.9
  const max = Math.max(...data) * 1.1 || 10
  const range = max - min || 1

  const padding = 24
  const chartW = width - padding * 2
  const chartH = height - padding * 2

  // Draw grid
  ctx.strokeStyle = 'rgba(150, 150, 150, 0.15)'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(padding, padding + chartH / 2)
  ctx.lineTo(padding + chartW, padding + chartH / 2)
  ctx.stroke()

  // Draw line points
  const points = data.map((val, idx) => {
    const x = padding + (idx / (data.length - 1)) * chartW
    const y = padding + chartH - ((val - min) / range) * chartH
    return { x, y, val }
  })

  // Gradient fill
  const grad = ctx.createLinearGradient(0, padding, 0, padding + chartH)
  grad.addColorStop(0, 'rgba(225, 29, 72, 0.25)')
  grad.addColorStop(1, 'rgba(225, 29, 72, 0.0)')

  ctx.fillStyle = grad
  ctx.beginPath()
  ctx.moveTo(points[0].x, padding + chartH)
  points.forEach(p => ctx.lineTo(p.x, p.y))
  ctx.lineTo(points[points.length - 1].x, padding + chartH)
  ctx.closePath()
  ctx.fill()

  // Line stroke
  ctx.strokeStyle = '#e11d48'
  ctx.lineWidth = 2.5
  ctx.beginPath()
  points.forEach((p, i) => {
    if (i === 0) ctx.moveTo(p.x, p.y)
    else ctx.lineTo(p.x, p.y)
  })
  ctx.stroke()

  // Dots
  points.forEach(p => {
    ctx.fillStyle = '#ffffff'
    ctx.strokeStyle = '#e11d48'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(p.x, p.y, 4, 0, Math.PI * 2)
    ctx.fill()
    ctx.stroke()
  })
}
</script>
