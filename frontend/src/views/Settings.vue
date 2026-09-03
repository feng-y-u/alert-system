<template>
  <div class="page">
    <SectionCard
      title="邮件告警配置"
      subtitle="用于把异常登录告警推送到管理员邮箱"
    >
      <template #actions>
        <el-button :loading="loading" @click="fetchConfig">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </template>

      <div v-loading="loading" class="email-config">
        <template v-if="!loading">
          <!-- 状态总览 -->
          <div class="status-banner" :class="config.configured ? 'is-ok' : 'is-off'">
            <span class="status-banner__icon">
              <el-icon :size="18">
                <CircleCheckFilled v-if="config.configured" />
                <WarningFilled v-else />
              </el-icon>
            </span>
            <div class="status-banner__text">
              <strong>{{ config.configured ? 'SMTP 已配置' : 'SMTP 未配置' }}</strong>
              <span v-if="config.configured">
                告警生成后会自动发送到全部启用中的管理员邮箱
              </span>
              <span v-else>
                在 <code>backend/.env</code> 中填写真实 SMTP 凭据后自动生效，无需改代码
              </span>
            </div>
          </div>

          <p v-if="config.note" class="note">
            <el-icon><InfoFilled /></el-icon>
            {{ config.note }}
          </p>

          <!-- 配置明细 -->
          <dl class="config-list">
            <div v-for="row in configRows" :key="row.label" class="config-row">
              <dt>{{ row.label }}</dt>
              <dd>
                <span v-if="row.tag" class="pill" :class="`pill--${row.tone}`">
                  {{ row.value }}
                </span>
                <span v-else class="mono">{{ row.value }}</span>
              </dd>
            </div>
          </dl>

          <!-- 测试发送 -->
          <div class="actions">
            <el-button
              type="primary"
              :loading="sending"
              :disabled="!config.configured"
              @click="handleTest"
            >
              <el-icon><Promotion /></el-icon>
              {{ sending ? '正在发送…' : '发送测试邮件' }}
            </el-button>
            <span v-if="!config.configured" class="actions__hint">
              配置 SMTP 后可用
            </span>
          </div>

          <Transition name="slide">
            <div
              v-if="testResult"
              class="result"
              :class="testResult.success ? 'is-ok' : 'is-error'"
            >
              <el-icon :size="17">
                <CircleCheckFilled v-if="testResult.success" />
                <CircleCloseFilled v-else />
              </el-icon>
              <span>{{ testResult.message }}</span>
            </div>
          </Transition>
        </template>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { getEmailConfig, testEmail } from '../api/settings'
import { useAsyncData } from '../composables/useAsyncData'
import SectionCard from '../components/common/SectionCard.vue'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  InfoFilled,
  Promotion,
  Refresh,
  WarningFilled,
} from '@element-plus/icons-vue'

const config = ref({
  configured: false,
  host: '',
  port: 0,
  has_user: false,
  from_addr: '',
  note: '',
})

const sending = ref(false)
const testResult = ref(null)

async function fetchConfig() {
  const res = await getEmailConfig()
  config.value = res
}

// 拉取失败时给出一份明确的兜底状态，而不是让页面卡在 loading
const { loading, execute } = useAsyncData(async () => {
  try {
    await fetchConfig()
  } catch {
    config.value = {
      configured: false,
      host: '',
      port: 0,
      has_user: false,
      from_addr: '',
      note: '获取配置失败，请检查后端服务是否正常',
    }
  }
})

onMounted(execute)

const configRows = computed(() => [
  { label: '配置状态', value: config.value.configured ? '已配置' : '未配置', tag: true, tone: config.value.configured ? 'ok' : 'off' },
  { label: 'SMTP 服务器', value: config.value.host || '—' },
  { label: '端口', value: config.value.port || '—' },
  { label: '账号', value: config.value.has_user ? '已设置' : '未设置', tag: true, tone: config.value.has_user ? 'ok' : 'off' },
  { label: '发件人地址', value: config.value.from_addr || '—' },
])

async function handleTest() {
  sending.value = true
  testResult.value = null
  try {
    testResult.value = await testEmail()
  } catch (err) {
    const detail = err.response?.data?.detail || err.message || '请求失败'
    testResult.value = { success: false, message: `发送失败：${detail}` }
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.page {
  max-width: 780px;
}

.email-config {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* 状态横幅 */
.status-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 15px 17px;
  border-radius: var(--r-md);
}

.status-banner.is-ok {
  background: var(--success-soft);
}

.status-banner.is-off {
  background: var(--warning-soft);
}

.status-banner__icon {
  display: flex;
  padding-top: 1px;
}

.status-banner.is-ok .status-banner__icon {
  color: var(--success-ink);
}

.status-banner.is-off .status-banner__icon {
  color: var(--warning-ink);
}

.status-banner__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 13px;
  line-height: 1.6;
}

.status-banner.is-ok .status-banner__text {
  color: var(--success-ink);
}

.status-banner.is-off .status-banner__text {
  color: var(--warning-ink);
}

.status-banner__text strong {
  font-size: 14px;
  font-weight: 600;
}

.status-banner__text code {
  padding: 1px 5px;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.7);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.note {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 10px 14px;
  border-radius: var(--r-sm);
  background: var(--bg-subtle);
  border: 1px dashed var(--border);
  font-size: 13px;
  color: var(--text-muted);
}

/* 配置明细 */
.config-list {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border-soft);
  border-radius: var(--r-md);
  overflow: hidden;
}

.config-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 13px 17px;
  background: var(--bg-surface);
  transition: background var(--dur) var(--ease);
}

.config-row:hover {
  background: var(--bg-subtle);
}

.config-row + .config-row {
  border-top: 1px solid var(--border-soft);
}

.config-row dt {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
  flex-shrink: 0;
}

.config-row dd {
  font-size: 14px;
  color: var(--text-strong);
  text-align: right;
  min-width: 0;
  word-break: break-all;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: var(--r-full);
  font-size: 12px;
  font-weight: 600;
}

.pill--ok {
  background: var(--success-soft);
  color: var(--success-ink);
}

.pill--off {
  background: var(--bg-hover);
  color: var(--text-muted);
}

/* 操作区 */
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 4px;
}

.actions__hint {
  font-size: 12px;
  color: var(--text-faint);
}

.result {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 15px;
  border-radius: var(--r-sm);
  font-size: 14px;
}

.result.is-ok {
  background: var(--success-soft);
  color: var(--success-ink);
}

.result.is-error {
  background: var(--danger-soft);
  color: var(--danger-ink);
}

.slide-enter-active {
  animation: slide-in 0.25s var(--ease);
}

@keyframes slide-in {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
