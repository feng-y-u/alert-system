<template>
  <div class="change-password">
    <div class="card">
      <h1>修改初始密码</h1>
      <p class="hint">
        默认管理员口令是公开的示例值，首次登录后必须先修改密码才能使用其它功能。
      </p>

      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label for="old-password">当前密码</label>
          <input
            id="old-password"
            v-model="form.oldPassword"
            type="password"
            autocomplete="current-password"
            placeholder="请输入当前密码"
          />
        </div>
        <div class="form-group">
          <label for="new-password">新密码（至少 8 位）</label>
          <input
            id="new-password"
            v-model="form.newPassword"
            type="password"
            autocomplete="new-password"
            placeholder="请输入新密码"
          />
        </div>
        <div class="form-group">
          <label for="confirm-password">确认新密码</label>
          <input
            id="confirm-password"
            v-model="form.confirmPassword"
            type="password"
            autocomplete="new-password"
            placeholder="请再次输入新密码"
          />
        </div>

        <p v-if="error" class="error-msg">{{ error }}</p>

        <button class="btn-primary" type="submit" :disabled="loading">
          {{ loading ? '提交中…' : '提交并进入系统' }}
        </button>
        <button class="btn-link" type="button" @click="handleLogout">退出登录</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' })
const loading = ref(false)
const error = ref('')

function validate() {
  if (!form.oldPassword || !form.newPassword) {
    return '请填写当前密码与新密码'
  }
  if (form.newPassword.length < 8) {
    return '新密码长度至少 8 位'
  }
  if (form.newPassword !== form.confirmPassword) {
    return '两次输入的新密码不一致'
  }
  if (form.newPassword === form.oldPassword) {
    return '新密码不能与当前密码相同'
  }
  return ''
}

async function handleSubmit() {
  const message = validate()
  if (message) {
    error.value = message
    return
  }

  loading.value = true
  error.value = ''
  try {
    await authStore.changePassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码修改成功')
    router.push('/')
  } catch (err) {
    const detail = err.response?.data?.detail
    error.value = Array.isArray(detail) ? detail.map((d) => d.msg).join('；') : detail || '修改失败，请重试'
  } finally {
    loading.value = false
  }
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.change-password {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-app);
}

.card {
  width: 100%;
  max-width: 420px;
  padding: 32px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: 16px;
}

h1 {
  margin: 0 0 8px;
  font-size: 20px;
  color: var(--text-strong);
}

.hint {
  margin: 0 0 20px;
  font-size: 13px;
  color: var(--text-muted);
  line-height: 1.6;
}

.form-group {
  margin-bottom: 16px;
}

label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  color: var(--text-body);
}

input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 14px;
  background: var(--bg-surface);
  color: var(--text-strong);
}

input:focus {
  outline: none;
  border-color: var(--el-color-primary);
}

.error-msg {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--el-color-danger);
}

.btn-primary {
  width: 100%;
  height: 40px;
  border: none;
  border-radius: 8px;
  background: var(--el-color-primary);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-link {
  width: 100%;
  margin-top: 10px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
}
</style>
