import api from './index'

export function getEmailConfig() {
  return api.get('/api/settings/email')
}

export function testEmail() {
  return api.post('/api/settings/email/test')
}
