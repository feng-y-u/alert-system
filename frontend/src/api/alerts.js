import api from './index'

export function getAlerts(params) {
  return api.get('/api/alerts', { params })
}

export function updateAlertStatus(alertId, status) {
  return api.put(`/api/alerts/${alertId}`, { status })
}

export function clearAlerts(scope) {
  // confirm=true：后端自 P1-4 起要求销毁类操作显式确认，否则返回 409
  return api.delete('/api/alerts', { params: { scope, confirm: true } })
}
