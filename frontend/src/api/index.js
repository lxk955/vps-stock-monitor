const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

async function request(url, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  // Attach Admin JWT Token if present
  const adminToken = localStorage.getItem('vps_admin_token')
  if (adminToken && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${adminToken}`
  }

  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorDetail = '网络请求失败'
    try {
      const errJson = await response.json()
      errorDetail = errJson.detail || errJson.message || errorDetail
    } catch {
      errorDetail = response.statusText
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export const api = {
  // Stats
  getStats: () => request('/stats'),

  // Products
  getProducts: (params = {}, options = {}) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        query.append(key, val)
      }
    })
    const qs = query.toString()
    return request(`/products${qs ? `?${qs}` : ''}`, options)
  },
  getFacets: () => request('/products/facets'),
  getProduct: (id) => request(`/products/${id}`),
  getPriceHistory: (id) => request(`/products/${id}/price-history`),
  recordClick: (id) => request(`/products/${id}/click`, { method: 'POST' }),
  createProduct: (data) => request('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id) => request(`/products/${id}`, { method: 'DELETE' }),

  // Subscriptions (Watchlist)
  subscribe: (data) => request('/subscriptions', { method: 'POST', body: JSON.stringify(data) }),
  getMySubscriptions: (params = {}) => {
    const query = new URLSearchParams()
    Object.entries(params).forEach(([key, val]) => {
      if (val) query.append(key, val)
    })
    const qs = query.toString()
    return request(`/subscriptions/my${qs ? `?${qs}` : ''}`)
  },
  updateSubscription: (id, data, token) => {
    const query = new URLSearchParams()
    if (token) query.append('token', token)
    const qs = query.toString()
    return request(`/subscriptions/${id}${qs ? `?${qs}` : ''}`, { method: 'PUT', body: JSON.stringify(data) })
  },
  unsubscribe: (id, token) => {
    const query = new URLSearchParams()
    if (token) query.append('token', token)
    const qs = query.toString()
    return request(`/subscriptions/${id}${qs ? `?${qs}` : ''}`, { method: 'DELETE' })
  },
  requestMagicLink: (email) => request('/subscriptions/request-link', { method: 'POST', body: JSON.stringify({ email }) }),

  // Settings
  getSettings: () => request('/settings'),
  updateSettings: (data) => request('/settings', { method: 'PUT', body: JSON.stringify(data) }),
  testSmtp: (test_email) => request('/settings/test-email', { method: 'POST', body: JSON.stringify({ test_email }) }),
  verifyAdmin: (password) => request('/settings/verify-admin', { method: 'POST', body: JSON.stringify({ password }) }),
  getAlertLogs: (limit = 50) => request(`/settings/alert-logs?limit=${limit}`),

  // Crawler
  triggerCrawler: () => request('/crawler/trigger', { method: 'POST' }),
  getCrawlerStatus: () => request('/crawler/status'),
}
