<template>
  <div class="login">
    <!-- 左侧品牌区（浅色渐变） -->
    <section class="login__brand">
      <div class="brand-deco brand-deco--a" />
      <div class="brand-deco brand-deco--b" />
      <div class="brand-grid" />

      <div class="brand-inner">
        <div class="brand-logo">
          <span class="brand-logo__mark">
            <el-icon :size="19"><Lock /></el-icon>
          </span>
          <span class="brand-logo__name">校园监测平台</span>
        </div>

        <h1 class="brand-title">
          守护每一次<br />
          校园账号登录
        </h1>
        <p class="brand-desc">
          实时采集校园系统登录日志，自动识别异常行为，第一时间把告警送到管理员手中。
        </p>

        <ul class="brand-list">
          <li v-for="f in features" :key="f">
            <span class="brand-list__icon">
              <el-icon :size="12"><Select /></el-icon>
            </span>
            {{ f }}
          </li>
        </ul>
      </div>

      <div class="brand-stats">
        <div v-for="s in highlights" :key="s.label" class="brand-stat">
          <span class="brand-stat__value num">{{ s.value }}</span>
          <span class="brand-stat__label">{{ s.label }}</span>
        </div>
      </div>
    </section>

    <!-- 右侧表单区 -->
    <section class="login__form">
      <div class="form-card">
        <div class="form-head">
          <span class="form-head__mark">
            <el-icon :size="16"><Lock /></el-icon>
          </span>
          <h2 class="form-title">管理员登录</h2>
          <p class="form-subtitle">请使用管理员账号登录以进入控制台</p>
        </div>

        <form class="form" @submit.prevent="handleLogin">
          <div class="field">
            <label class="field__label" for="username">用户名</label>
            <div class="field__control">
              <el-icon class="field__icon"><User /></el-icon>
              <input
                id="username"
                v-model="form.username"
                class="field__input"
                type="text"
                placeholder="请输入用户名"
                autocomplete="username"
                :disabled="loading"
              />
            </div>
          </div>

          <div class="field">
            <label class="field__label" for="password">密码</label>
            <div class="field__control">
              <el-icon class="field__icon"><Lock /></el-icon>
              <input
                id="password"
                v-model="form.password"
                class="field__input"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                autocomplete="current-password"
                :disabled="loading"
              />
              <button
                type="button"
                class="field__suffix"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
              >
                <el-icon :size="16">
                  <View v-if="!showPassword" />
                  <Hide v-else />
                </el-icon>
              </button>
            </div>
          </div>

          <Transition name="shake">
            <p v-if="error" class="form-error">
              <el-icon><WarningFilled /></el-icon>
              {{ error }}
            </p>
          </Transition>

          <button class="submit" type="submit" :disabled="loading">
            <span v-if="!loading">登 录</span>
            <span v-else class="submit__loading">
              <el-icon class="spin"><Loading /></el-icon>
              正在验证…
            </span>
          </button>
        </form>

        <p class="form-foot">
          默认账号 <code>admin</code> / <code>admin123</code>
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  Hide,
  Loading,
  Lock,
  Select,
  User,
  View,
  WarningFilled,
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const features = ['实时登录监控', '异常行为检测', '多渠道告警通知']
const highlights = [
  { value: '5min', label: '频率检测窗口' },
  { value: '24h', label: '告警去重周期' },
  { value: 'SSE', label: '实时推送' },
]

async function handleLogin() {
  if (!form.username.trim() || !form.password) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''
  try {
    await authStore.login(form.username.trim(), form.password)
    router.push('/')
  } catch (err) {
    const detail = err.response?.data?.detail
    error.value = Array.isArray(detail)
      ? detail.map((d) => d.msg).join('；')
      : detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login {
  display: flex;
  min-height: 100vh;
  background: var(--bg-app);
}

/* ============ 品牌区（浅色渐变 + 装饰色晕） ============ */
.login__brand {
  flex: 1.1;
  position: relative;
  overflow: hidden;
  background: linear-gradient(150deg, #e8f1ff 0%, #f2f7ff 48%, #eaf6ff 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 56px 64px;
}

.brand-deco {
  position: absolute;
  border-radius: 50%;
  filter: blur(2px);
  pointer-events: none;
}

.brand-deco--a {
  top: -140px;
  right: -120px;
  width: 380px;
  height: 380px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.14), transparent 68%);
}

.brand-deco--b {
  bottom: -160px;
  left: -120px;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.12), transparent 68%);
}

/* 网格底纹 */
.brand-grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(
      to right,
      rgba(37, 99, 235, 0.05) 1px,
      transparent 1px
    ),
    linear-gradient(to bottom, rgba(37, 99, 235, 0.05) 1px, transparent 1px);
  background-size: 44px 44px;
  mask-image: radial-gradient(80% 60% at 30% 30%, #000 0%, transparent 100%);
}

.brand-inner {
  position: relative;
  max-width: 520px;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 56px;
}

.brand-logo__mark {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 18px rgba(37, 99, 235, 0.3);
}

.brand-logo__name {
  font-size: 18px;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: var(--text-strong);
}

.brand-title {
  font-size: 40px;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: -0.01em;
  margin-bottom: 18px;
  color: var(--text-strong);
}

.brand-desc {
  font-size: 15px;
  line-height: 1.75;
  color: var(--text-muted);
  margin-bottom: 36px;
}

.brand-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.brand-list li {
  display: flex;
  align-items: center;
  gap: 11px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-body);
}

.brand-list__icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  color: var(--brand-600);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-xs);
}

.brand-stats {
  position: relative;
  display: flex;
  gap: 40px;
  padding-top: 28px;
  border-top: 1px solid rgba(37, 99, 235, 0.12);
}

.brand-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.brand-stat__value {
  font-size: 20px;
  font-weight: 700;
  color: var(--brand-700);
}

.brand-stat__label {
  font-size: 12px;
  color: var(--text-faint);
}

/* ============ 表单区 ============ */
.login__form {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
  background: var(--bg-surface);
}

.form-card {
  width: 100%;
  max-width: 392px;
}

.form-head {
  margin-bottom: 28px;
}

.form-head__mark {
  display: none;
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: #fff;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.28);
}

.form-title {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-strong);
  letter-spacing: -0.01em;
  margin-bottom: 6px;
}

.form-subtitle {
  font-size: 14px;
  color: var(--text-muted);
}

.form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 7px;
}

.field__label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-body);
}

.field__control {
  position: relative;
  display: flex;
  align-items: center;
}

.field__icon {
  position: absolute;
  left: 13px;
  color: var(--text-faint);
  font-size: 16px;
  pointer-events: none;
}

.field__input {
  width: 100%;
  height: 46px;
  padding: 0 42px;
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  background: var(--bg-surface);
  font-size: 14px;
  color: var(--text-strong);
  transition: border-color var(--dur) var(--ease), box-shadow var(--dur) var(--ease);
}

.field__input::placeholder {
  color: var(--text-faint);
}

.field__input:focus {
  outline: none;
  border-color: var(--brand-500);
  box-shadow: 0 0 0 3px var(--brand-100);
}

.field__input:disabled {
  background: var(--bg-subtle);
  cursor: not-allowed;
}

.field__suffix {
  position: absolute;
  right: 8px;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  color: var(--text-faint);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--dur) var(--ease);
}

.field__suffix:hover {
  background: var(--bg-hover);
  color: var(--text-body);
}

.form-error {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 13px;
  border-radius: var(--r-sm);
  background: var(--danger-soft);
  color: var(--danger-ink);
  font-size: 13px;
}

.submit {
  height: 46px;
  margin-top: 4px;
  border-radius: var(--r-sm);
  background: linear-gradient(135deg, var(--brand-500), var(--brand-600));
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.06em;
  transition: box-shadow var(--dur) var(--ease), transform var(--dur) var(--ease);
  box-shadow: 0 6px 16px rgba(37, 99, 235, 0.3);
}

.submit:hover:not(:disabled) {
  box-shadow: 0 8px 22px rgba(37, 99, 235, 0.38);
  transform: translateY(-1px);
}

.submit:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  box-shadow: none;
}

.submit__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.spin {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.form-foot {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-soft);
  text-align: center;
  font-size: 12px;
  color: var(--text-faint);
}

.form-foot code {
  padding: 2px 6px;
  border-radius: 6px;
  background: var(--bg-hover);
  color: var(--text-body);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.shake-enter-active {
  animation: shake 0.35s var(--ease);
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-5px); }
  75% { transform: translateX(5px); }
}

@media (max-width: 1024px) {
  .login__brand {
    display: none;
  }

  .form-head__mark {
    display: flex;
  }

  .login__form {
    padding: 32px 20px;
    background: var(--bg-app);
  }
}
</style>
