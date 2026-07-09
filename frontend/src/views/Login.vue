<template>
  <div class="login-page">
    <div class="login-wrapper">
      <!-- 左侧品牌区 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="logo">
            <div class="logo-icon">TF</div>
            <span class="logo-text">校园监测平台</span>
          </div>
          <h1 class="brand-title">安全审计与日志分析系统</h1>
          <p class="brand-desc">
            监测校园系统的登录行为，检测异常登录并发送告警，保障校园账号安全。
          </p>
          <div class="brand-features">
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>实时登录监控</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>异常行为检测</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>智能告警通知</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2 class="form-title">欢迎回来</h2>
            <p class="form-subtitle">请使用管理员账号登录</p>
          </div>

          <form class="login-form" @submit.prevent="handleLogin">
            <div class="form-group">
              <label class="form-label">用户名</label>
              <div class="input-wrapper">
                <el-icon class="input-icon"><User /></el-icon>
                <input
                  v-model="form.username"
                  type="text"
                  placeholder="请输入用户名"
                  class="form-input"
                  @keyup.enter="handleLogin"
                />
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">密码</label>
              <div class="input-wrapper">
                <el-icon class="input-icon"><Lock /></el-icon>
                <input
                  v-model="form.password"
                  type="password"
                  placeholder="请输入密码"
                  class="form-input"
                  @keyup.enter="handleLogin"
                />
              </div>
            </div>

            <div v-if="error" class="error-message">
              <el-icon><Warning /></el-icon>
              <span>{{ error }}</span>
            </div>

            <button
              type="submit"
              class="submit-btn"
              :disabled="loading"
              :class="{ loading: loading }"
            >
              <span v-if="!loading">登录</span>
              <span v-else>登录中...</span>
            </button>
          </form>

          <div class="form-footer">
            <p>默认账号: <strong>admin</strong> / <strong>admin123</strong></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { User, Lock, Check, Warning } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  username: '',
  password: '',
})

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!form.username || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      error.value = detail.map(d => d.msg).join('；')
    } else {
      error.value = detail || '登录失败，请检查用户名和密码'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  background-color: var(--color-bg);
}

.login-wrapper {
  display: flex;
  width: 100%;
  min-height: 100vh;
}

/* === 左侧品牌区 === */
.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  position: relative;
  overflow: hidden;
}

.brand-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.5;
}

.brand-content {
  max-width: 480px;
  color: white;
  position: relative;
  z-index: 1;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 48px;
}

.logo-icon {
  width: 44px;
  height: 44px;
  background: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #111827;
  font-weight: 700;
  font-size: 16px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
}

.brand-title {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 16px;
}

.brand-desc {
  font-size: 16px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 48px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.9);
}

.feature-item .el-icon {
  width: 24px;
  height: 24px;
  background: rgba(16, 185, 129, 0.2);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #10b981;
  font-size: 14px;
}

/* === 右侧表单区 === */
.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
}

.form-container {
  width: 100%;
  max-width: 400px;
}

.form-header {
  margin-bottom: 32px;
}

.form-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 8px;
}

.form-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  font-size: 18px;
}

.form-input {
  width: 100%;
  height: 48px;
  padding: 0 16px 0 44px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.1);
}

.form-input::placeholder {
  color: var(--color-text-tertiary);
}

.error-message {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background-color: var(--color-danger-light);
  border-radius: 8px;
  color: var(--color-danger);
  font-size: 13px;
}

.error-message .el-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.submit-btn {
  height: 48px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 8px;
}

.submit-btn:hover:not(:disabled) {
  background: var(--color-primary-light);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.form-footer {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
  text-align: center;
  font-size: 13px;
  color: var(--color-text-secondary);
}

.form-footer strong {
  color: var(--color-text-primary);
  font-weight: 600;
}

/* === 响应式 === */
@media (max-width: 1024px) {
  .brand-section {
    display: none;
  }

  .form-section {
    padding: 24px;
  }
}
</style>