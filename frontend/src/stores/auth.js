import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  async function login(loginUsername, password) {
    const res = await api.post('/api/auth/login', {
      username: loginUsername,
      password,
    })
    token.value = res.access_token
    username.value = loginUsername
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('username', loginUsername)
    return res
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  function isLoggedIn() {
    return !!token.value
  }

  return { token, username, login, logout, isLoggedIn }
})