import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElNotification } from 'element-plus'
import { getAlerts } from '../api/alerts'

const typeMap = { frequency: '频率异常', device: '设备异常' }
const severityMap = { low: '低', medium: '中', high: '高' }

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  const isConnected = ref(false)
  /**
   * 已经计入未读的告警 id。
   *
   * 没有这个集合时，断网恢复后的补拉会把「同一批 pending 告警」重复累加
   * （断一次网就多算一遍），徽标数值会虚高到与真实待处理数无关（BUG-004）。
   * 用集合做幂等计数，SSE 推送与补拉都不会重复。
   */
  const seenAlertIds = new Set()
  let eventSource = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  const MAX_RECONNECT_ATTEMPTS = 10

  /** 只关闭连接，不改动重连计数与未读计数 */
  function closeSource() {
    isConnected.value = false
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  /** 幂等计入未读：同一个 alert_id 只加一次 */
  function markUnread(alertId) {
    if (alertId === null || alertId === undefined) return
    if (seenAlertIds.has(alertId)) return
    seenAlertIds.add(alertId)
    unreadCount.value += 1
  }

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
        markUnread(alert.alert_id)
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

      // 超过上限：彻底停止重连（保留 isConnected=false，界面显示「离线」）。
      // 这里必须用 closeSource() 而不是 disconnect() —— disconnect() 会把
      // reconnectAttempts 归零，导致计数永远到不了上限、无限重连（BUG-006）。
      if (reconnectAttempts > MAX_RECONNECT_ATTEMPTS) {
        closeSource()
        return
      }

      // EventSource 自身也会重连，避免叠加手动重连
      if (reconnectTimer) return

      reconnectTimer = setTimeout(() => {
        reconnectTimer = null
        closeSource() // 清连接但**不**重置计数
        connect(token)
      }, Math.min(reconnectAttempts * 2000, 10000))
    }
  }

  /** 用户主动断开（退出登录 / 离开主布局）：彻底复位，避免状态泄漏到下一个会话 */
  function disconnect() {
    closeSource()
    reconnectAttempts = 0
    unreadCount.value = 0
    // 必须清空：否则换一个管理员登录后，上一会话「已计入」的告警 id
    // 会让补拉静默跳过，新会话看不到应有的未读徽标。
    seenAlertIds.clear()
  }

  /**
   * 断网恢复后补拉最新待处理告警。
   *
   * 不接收 token：``getAlerts`` 走 axios 实例，Authorization 头由请求拦截器
   * 从 localStorage 自动附加。
   */
  async function fetchLatestAlertsOnReconnect() {
    try {
      const res = await getAlerts({ limit: 10, status: 'pending' })
      // markUnread 幂等：同一批告警重复补拉不会重复计数（BUG-004）
      ;(res?.items ?? []).forEach((item) => markUnread(item.id))
    } catch {
      // 静默失败，SSE 会自动推送
    }
  }

  function clearUnread() {
    unreadCount.value = 0
    // 刻意不清空 seenAlertIds：否则已看过的告警会在下次断网重连时被重复计入
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
