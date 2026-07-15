import { ref } from 'vue'

export function useRetry(fetchFn, { cooldownMs = 5000 } = {}) {
  const loading = ref(false)
  const error = ref(false)
  const retryCooldown = ref(false)

  let timer = null

  async function execute() {
    if (retryCooldown.value) return
    loading.value = true
    error.value = false
    try {
      await fetchFn()
    } catch {
      error.value = true
      retryCooldown.value = true
      timer = setTimeout(() => {
        retryCooldown.value = false
      }, cooldownMs)
    } finally {
      loading.value = false
    }
  }

  function cleanup() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  return { loading, error, retryCooldown, execute, cleanup }
}
