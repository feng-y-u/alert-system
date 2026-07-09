import api from './index'

export function getLogs(params) {
  return api.get('/api/logs', { params })
}