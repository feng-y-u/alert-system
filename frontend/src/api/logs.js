import api from './index'

export function getLogs(params) {
  return api.get('/api/logs', { params })
}

export function clearLogs() {
  // confirm=true：后端自 P1-4 起要求销毁类操作显式确认，否则返回 409
  return api.delete('/api/logs', { params: { confirm: true } })
}
