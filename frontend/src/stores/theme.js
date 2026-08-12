import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // Themes: 'sakura' | 'light' | 'dark' | 'system'
  const currentTheme = ref(localStorage.getItem('vps_theme') || 'sakura')

  function applyTheme(theme) {
    const root = document.documentElement
    root.removeAttribute('data-theme')
    root.classList.remove('dark')

    if (theme === 'system') {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      if (prefersDark) {
        root.classList.add('dark')
      }
      root.setAttribute('data-theme', 'system')
    } else if (theme === 'dark') {
      root.classList.add('dark')
      root.setAttribute('data-theme', 'dark')
    } else if (theme === 'sakura') {
      root.setAttribute('data-theme', 'sakura')
    } else {
      root.setAttribute('data-theme', 'light')
    }
  }

  function setTheme(theme) {
    currentTheme.value = theme
    localStorage.setItem('vps_theme', theme)
    applyTheme(theme)
  }

  // Init
  applyTheme(currentTheme.value)

  // Listen to OS theme changes if on system mode
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    if (currentTheme.value === 'system') {
      applyTheme('system')
    }
  })

  return {
    currentTheme,
    setTheme,
  }
})
