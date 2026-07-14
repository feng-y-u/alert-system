import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElNotification } from 'element-plus'

const typeMap = { frequency: '频率异常', device: '设备异常' }
const severityMap = { low: '低', medium: '中', high: '高' }

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  let eventSource = null

  function connect(token) {
    if (eventSource) return

    eventSource = new EventSource(`/api/notifications/stream?token=${token}`)

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
      // 浏览器自动重连
    }
  }

  function clearUnread() {
    unreadCount.value = 0
  }

  function disconnect() {
    eventSource?.close()
    eventSource = null
    unreadCount.value = 0
  }

  return { unreadCount, connect, clearUnread, disconnect }
})
