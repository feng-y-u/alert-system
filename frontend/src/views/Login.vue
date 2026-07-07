<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>校园监测平台</h2>
      <p class="login-desc">管理员登录</p>
      <el-form :model="form" label-width="80px" @keyup.enter="handleLogin">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin">
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <p v-if="error" class="error-msg">{{ error }}</p>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

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
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: #f0f2f5;
}

.login-card {
  width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 4px;
}

.login-desc {
  text-align: center;
  color: #999;
  margin-bottom: 20px;
  font-size: 14px;
}

.error-msg {
  color: #f56c6c;
  text-align: center;
  font-size: 14px;
}
</style>