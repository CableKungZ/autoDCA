import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const plansApi = {
  list: () => api.get('/plans'),
  create: (data: any) => api.post('/plans', data),
  get: (id: string) => api.get(`/plans/${id}`),
  update: (id: string, data: any) => api.patch(`/plans/${id}`, data),
  pause: (id: string) => api.post(`/plans/${id}/pause`),
  resume: (id: string) => api.post(`/plans/${id}/resume`),
  delete: (id: string) => api.delete(`/plans/${id}`),
  trigger: (id: string) => api.post(`/plans/${id}/trigger`),
  symbols: (exchange: string) => api.get('/plans/symbols', { params: { exchange } }),
}

export const ordersApi = {
  list: (params: any) => api.get('/orders', { params }),
  get: (id: string) => api.get(`/orders/${id}`),
  cancel: (id: string) => api.post(`/orders/${id}/cancel`),
  clearPending: () => api.post('/orders/clear-pending'),
  sell: (data: any) => api.post('/orders/sell', data),
}

export const statsApi = {
  summary: (params?: any) => api.get('/stats/summary', { params }),
  pnl: (params?: any) => api.get('/stats/pnl', { params }),
}

export const ratesApi = {
  list: (days = 30) => api.get('/rates', { params: { days } }),
  current: () => api.get('/rates/current'),
}

export const logsApi = {
  list: (params?: any) => api.get('/logs', { params }),
}
