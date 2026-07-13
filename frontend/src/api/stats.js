import api from './index'

export function getAlertStats(days = 7) {
  return api.get('/api/stats/alerts', { params: { days } })
}
