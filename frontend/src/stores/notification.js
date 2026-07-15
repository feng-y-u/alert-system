import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElNotification } from 'element-plus'
import { getAlerts } from '../api/alerts'

const typeMap = { frequency: '频率异常', device: '设备异常' }
const severityMap = { low: '低', medium: '中', high: '高' }

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const isConnected = ref(false)
  let eventSource = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  const MAX_RECONNECT_ATTEMPTS = 10

  function connect(token) {
    if (eventSource) return

    eventSource = new EventSource(`/api/notifications/stream?token=${token}`)

    eventSource.onopen = () => {
      isConnected.value = true
      reconnectAttempts = 0
    }

    eventSource.onmessage = (e) => {
      try {
        const alert = JSON.parse(e.data)
        unreadCount.value++
        ElNotification({
          title: '新告警',
          message: `${typeMap[alert.type] || alert.type} · ${severityMap[alert.severity] || alert.severity} · ${alert.username}`,
          type: alert.severity === 'high' ? 'error' : 'warning',
          duration: 5000,
        })
      } catch {
        // 解析失败跳过
      }
    }

    eventSource.onerror = () => {
      isConnected.value = false
      reconnectAttempts++

      if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
        disconnect()
        return
      }

      reconnectTimer = setTimeout(() => {
        disconnect()
        connect(token)
      }, Math.min(reconnectAttempts * 2000, 10000))
    }
  }

  function disconnect() {
    isConnected.value = false
    unreadCount.value = 0
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    reconnectAttempts = 0
  }

  async function fetchLatestAlertsOnReconnect(token) {
    try {
      const res = await getAlerts({ limit: 10, status: 'pending' })
      if (res.items && res.items.length > 0) {
        unreadCount.value += res.items.length
      }
    } catch {
      // 静默失败，SSE 会自动推送
    }
  }

  function clearUnread() {
    unreadCount.value = 0
  }

  return {
    unreadCount,
    isConnected,
    connect,
    disconnect,
    clearUnread,
    fetchLatestAlertsOnReconnect,
  }
})
