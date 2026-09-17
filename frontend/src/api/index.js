import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
})

function detailOf(error) {
  const detail = error.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg).join('；')
  }
  return detail
}

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  async (error) => {
    const status = error.response?.status
    const url = error.config?.url || ''
    // 登录接口自身的 401 是「用户名或密码错误」，必须交给调用方展示，
    // 不能被全局跳转吞掉（见 docs/tech/14-评估与改进.md P1-7）
    const isAuthEntry = url.includes('/api/auth/login') || url.includes('/api/auth/change-password')

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('username')
      localStorage.removeItem('mustChangePassword')
      if (!isAuthEntry) {
        ElMessage.warning('登录已过期，请重新登录')
        const { default: router } = await import('../router')
        if (router.currentRoute.value.path !== '/login') {
          router.push('/login')
        }
      }
      return Promise.reject(error)
    }

    if (status === 403) {
      const detail = detailOf(error)
      if (typeof detail === 'string' && detail.includes('初始密码')) {
        ElMessage.warning(detail)
        const { default: router } = await import('../router')
        router.push('/change-password')
      } else {
        ElMessage.error(detail || '无权限访问')
      }
    } else if (status === 409) {
      // 销毁类接口要求 confirm=true
      ElMessage.warning(detailOf(error) || '该操作需要二次确认')
    } else if (status >= 500) {
      ElMessage.error('服务器异常，请稍后重试')
    } else if (status === 429) {
      ElMessage.warning(detailOf(error) || '请求过于频繁，请稍后再试')
    } else if (status === 400 || status === 404 || status === 422) {
      ElMessage.error(detailOf(error) || '请求参数有误')
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请稍后重试')
    } else if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络')
    }

    return Promise.reject(error)
  }
)

export default api
