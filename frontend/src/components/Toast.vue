<template>
  <Transition
    enter-active-class="transform ease-out duration-300 transition"
    enter-from-class="translate-y-2 opacity-0 sm:translate-y-0 sm:translate-x-2"
    enter-to-class="translate-y-0 opacity-100 sm:translate-x-0"
    leave-active-class="transition ease-in duration-100"
    leave-from-class="opacity-100"
    leave-to-class="opacity-0"
  >
    <div
      v-if="visible"
      class="fixed bottom-5 right-5 z-[99999] flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl border text-sm font-medium animate-in fade-in slide-in-from-bottom-5 duration-200"
      :class="toastClasses"
    >
      <component :is="iconComponent" class="w-5 h-5 shrink-0" />
      <span>{{ message }}</span>
      <button @click="visible = false" class="ml-2 opacity-70 hover:opacity-100 transition-opacity">
        <X class="w-4 h-4" />
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed } from 'vue'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-vue-next'

const visible = ref(false)
const message = ref('')
const type = ref('success') // 'success' | 'error' | 'info'
let timer = null

function show(msg, toastType = 'success', duration = 3000) {
  message.value = msg
  type.value = toastType
  visible.value = true

  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    visible.value = false
  }, duration)
}

const iconComponent = computed(() => {
  if (type.value === 'success') return CheckCircle2
  if (type.value === 'error') return AlertCircle
  return Info
})

const toastClasses = computed(() => {
  if (type.value === 'success') {
    return 'bg-emerald-50 text-emerald-900 border-emerald-200 dark:bg-emerald-950/80 dark:text-emerald-200 dark:border-emerald-800'
  }
  if (type.value === 'error') {
    return 'bg-rose-50 text-rose-900 border-rose-200 dark:bg-rose-950/80 dark:text-rose-200 dark:border-rose-800'
  }
  return 'bg-slate-50 text-slate-900 border-slate-200 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-800'
})

defineExpose({ show })
</script>
