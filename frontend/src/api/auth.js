import api from './index'

export function login(username, password) {
  return api.post('/api/auth/login', { username, password })
}

export function changePassword(oldPassword, newPassword) {
  return api.post('/api/auth/change-password', {
    old_password: oldPassword,
    new_password: newPassword,
  })
}

export function getMe() {
  return api.get('/api/auth/me')
}
