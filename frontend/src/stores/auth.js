import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  // 初始口令未修改时为 true：除改密外所有接口都会 403（见 P1-6）
  const mustChangePassword = ref(localStorage.getItem('mustChangePassword') === '1')

  function _persist(newToken, newUsername, mustChange) {
    token.value = newToken
    username.value = newUsername
    mustChangePassword.value = mustChange
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUsername)
    localStorage.setItem('mustChangePassword', mustChange ? '1' : '0')
  }

  async function login(loginUsername, password) {
    const res = await authApi.login(loginUsername, password)
    _persist(res.access_token, loginUsername, !!res.must_change_password)
    return res
  }

  async function changePassword(oldPassword, newPassword) {
    const res = await authApi.changePassword(oldPassword, newPassword)
    // 后端返回新 token，且 must_change_password 已置为 false
    _persist(res.access_token, username.value, !!res.must_change_password)
    return res
  }

  function logout() {
    token.value = ''
    username.value = ''
    mustChangePassword.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('mustChangePassword')
  }

  function isLoggedIn() {
    return !!token.value
  }

  return {
    token,
    username,
    mustChangePassword,
    login,
    changePassword,
    logout,
    isLoggedIn,
  }
})
