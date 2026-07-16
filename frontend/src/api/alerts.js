import api from './index'

export function getAlerts(params) {
  return api.get('/api/alerts', { params })
}

export function updateAlertStatus(alertId, status) {
  return api.put(`/api/alerts/${alertId}`, { status })
}

export function clearAlerts(scope) {
  return api.delete('/api/alerts', { params: { scope } })
}
