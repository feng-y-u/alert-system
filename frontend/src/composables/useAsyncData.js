import { onUnmounted, ref } from 'vue'

/**
 * 统一的异步数据加载状态机。
 *
 * 解决的问题：登录日志页与告警页此前各复制了一份
 * loading / error / retryCooldown / retryTimer 四件套，且都要手写 onUnmounted 清理。
 *
 * @param {Function} fetchFn 真正的取数函数，抛错即视为失败
 * @param {{ cooldownMs?: number, immediate?: boolean }} options
 */
export function useAsyncData(fetchFn, { cooldownMs = 5000, immediate = false } = {}) {
  const loading = ref(false)
  const error = ref(false)
  const retryCooldown = ref(false)

  let timer = null

  function clearTimer() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  async function execute() {
    if (retryCooldown.value) return
    loading.value = true
    error.value = false
    try {
      await fetchFn()
    } catch {
      error.value = true
      retryCooldown.value = true
      clearTimer()
      timer = setTimeout(() => {
        retryCooldown.value = false
      }, cooldownMs)
    } finally {
      loading.value = false
    }
  }

  onUnmounted(clearTimer)

  if (immediate) {
    execute()
  }

  return { loading, error, retryCooldown, execute }
}
