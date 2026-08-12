import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api'

export const useWatchlistStore = defineStore('watchlist', () => {
  // Safe JSON parse from localStorage
  let initialWatchlist = []
  try {
    const raw = localStorage.getItem('vps_user_watchlist')
    if (raw) initialWatchlist = JSON.parse(raw)
  } catch (err) {
    console.warn('Corrupted watchlist in localStorage, resetting to empty', err)
    localStorage.removeItem('vps_user_watchlist')
  }

  const localWatchlist = ref(initialWatchlist)
  const userEmail = ref(localStorage.getItem('vps_user_email') || '')
  const userToken = ref(localStorage.getItem('vps_user_token') || '')

  // Remote synced subscriptions
  const remoteSubscriptions = ref([])
  const isLoading = ref(false)

  const watchedProductIds = computed(() => {
    const localIds = localWatchlist.value.map(item => item.productId).filter(Boolean)
    const remoteIds = remoteSubscriptions.value.map(item => item.product_id).filter(Boolean)
    return Array.from(new Set([...localIds, ...remoteIds]))
  })

  function isWatched(productId) {
    return watchedProductIds.value.includes(productId)
  }

  function getWatchInfo(productId) {
    const fromRemote = remoteSubscriptions.value.find(s => s.product_id === productId)
    if (fromRemote) {
      return {
        id: fromRemote.id,
        productId: fromRemote.product_id,
        email: fromRemote.email,
        notifyStock: fromRemote.notify_stock,
        notifyPriceDrop: fromRemote.notify_price_drop,
        targetPrice: fromRemote.target_price,
        token: fromRemote.unsubscribe_token,
      }
    }
    return localWatchlist.value.find(item => item.productId === productId) || null
  }

  function saveLocal() {
    try {
      localStorage.setItem('vps_user_watchlist', JSON.stringify(localWatchlist.value))
      if (userEmail.value) localStorage.setItem('vps_user_email', userEmail.value)
      if (userToken.value) localStorage.setItem('vps_user_token', userToken.value)
    } catch (err) {
      console.warn('Failed to save to localStorage:', err)
    }
  }

  async function addWatch({ productId, email, notifyStock, notifyPriceDrop, targetPrice }) {
    const res = await api.subscribe({
      product_id: productId,
      email,
      notify_stock: notifyStock,
      notify_price_drop: notifyPriceDrop,
      target_price: targetPrice ? parseFloat(targetPrice) : null,
    })

    userEmail.value = email
    if (res.subscription?.unsubscribe_token) {
      userToken.value = res.subscription.unsubscribe_token
    }

    // Update local store
    const existingIdx = localWatchlist.value.findIndex(item => item.productId === productId)
    const entry = {
      id: res.subscription?.id,
      productId,
      email,
      notifyStock,
      notifyPriceDrop,
      targetPrice,
      token: res.subscription?.unsubscribe_token,
    }

    if (existingIdx >= 0) {
      localWatchlist.value[existingIdx] = entry
    } else {
      localWatchlist.value.push(entry)
    }

    saveLocal()
    await syncRemote()
    return res
  }

  async function removeWatch(productId) {
    const watchItem = getWatchInfo(productId)
    if (watchItem && watchItem.id) {
      try {
        await api.unsubscribe(watchItem.id, watchItem.token)
      } catch (err) {
        console.warn('Unsubscribe API error:', err)
      }
    }

    localWatchlist.value = localWatchlist.value.filter(item => item.productId !== productId)
    remoteSubscriptions.value = remoteSubscriptions.value.filter(item => item.product_id !== productId)
    saveLocal()
  }

  async function syncRemote() {
    if (!userEmail.value && !userToken.value) return
    isLoading.value = true
    try {
      const params = {}
      if (userToken.value) params.token = userToken.value
      else if (userEmail.value) params.email = userEmail.value
      const list = await api.getMySubscriptions(params)
      remoteSubscriptions.value = list
    } catch (err) {
      console.warn('Sync remote subscriptions error:', err)
    } finally {
      isLoading.value = false
    }
  }

  return {
    localWatchlist,
    remoteSubscriptions,
    userEmail,
    userToken,
    watchedProductIds,
    isLoading,
    isWatched,
    getWatchInfo,
    addWatch,
    removeWatch,
    syncRemote,
  }
})
