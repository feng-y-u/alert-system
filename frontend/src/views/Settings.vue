<template>
  <div class="settings-page">
    <div class="card">
      <div class="card-header">
        <div class="card-icon">
          <el-icon :size="20"><Setting /></el-icon>
        </div>
        <span class="card-title">邮件告警配置</span>
      </div>

      <div v-if="loading" class="loading-state">
        <el-icon class="loading-icon" :size="24"><Loading /></el-icon>
        <span>正在检查邮件配置...</span>
      </div>

      <div v-else class="config-detail">
        <div class="config-row">
          <span class="config-label">状态</span>
          <el-tag :type="config.configured ? 'success' : 'danger'" effect="plain">
            {{ config.configured ? '已配置' : '未配置' }}
          </el-tag>
        </div>

        <div class="config-row">
          <span class="config-label">SMTP 服务器</span>
          <span class="config-value">{{ config.host || '-' }}</span>
        </div>

        <div class="config-row">
          <span class="config-label">端口</span>
          <span class="config-value">{{ config.port || '-' }}</span>
        </div>

        <div class="config-row">
          <span class="config-label">账号</span>
          <el-tag :type="config.has_user ? 'success' : 'info'" effect="plain" size="small">
            {{ config.has_user ? '已设置' : '未设置' }}
          </el-tag>
        </div>

        <div class="config-row">
          <span class="config-label">发件人地址</span>
          <span class="config-value">{{ config.from_addr || '-' }}</span>
        </div>

        <div v-if="config.note" class="config-note">
          <el-icon :size="16"><Warning /></el-icon>
          <span>{{ config.note }}</span>
        </div>

        <div class="config-actions">
          <el-button
            type="primary"
            :loading="sending"
            :disabled="!config.configured"
            @click="handleTest"
          >
            {{ sending ? '发送中...' : '发送测试邮件' }}
          </el-button>
        </div>

        <div v-if="testResult" class="test-result" :class="{ success: testResult.success, error: !testResult.success }">
          <el-icon :size="18">
            <CircleCheck v-if="testResult.success" />
            <CircleClose v-else />
          </el-icon>
          <span>{{ testResult.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getEmailConfig, testEmail } from '../api/settings'
import { Setting, Loading, Warning, CircleCheck, CircleClose } from '@element-plus/icons-vue'

const loading = ref(true)
const sending = ref(false)
const config = ref({
  configured: false,
  host: '',
  port: 0,
  has_user: false,
  from_addr: '',
  note: '',
})
const testResult = ref(null)

async function fetchConfig() {
  try {
    const res = await getEmailConfig()
    config.value = res
  } catch {
    config.value = { configured: false, host: '', port: 0, has_user: false, from_addr: '', note: '获取配置失败' }
  } finally {
    loading.value = false
  }
}

async function handleTest() {
  sending.value = true
  testResult.value = null
  try {
    const res = await testEmail()
    testResult.value = res
  } catch (err) {
    const detail = err.response?.data?.detail || err.message || '请求失败'
    testResult.value = { success: false, message: `请求失败: ${detail}` }
  } finally {
    sending.value = false
  }
}

onMounted(fetchConfig)
</script>

<style scoped>
.settings-page {
  max-width: 640px;
}

.card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--color-border);
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 32px 0;
  justify-content: center;
  color: var(--color-text-secondary);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.config-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.config-label {
  font-size: 14px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.config-value {
  font-size: 14px;
  color: var(--color-text-primary);
  font-family: monospace;
}

.config-note {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #FEF3C7;
  border-radius: 8px;
  color: #92400E;
  font-size: 13px;
}

.config-actions {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.test-result {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-top: 12px;
}

.test-result.success {
  background: #D1FAE5;
  color: #065F46;
}

.test-result.error {
  background: #FEE2E2;
  color: #991B1B;
}
</style>
