<template>
  <div class="login-logs-page">
    <LogFilter @search="handleSearch" @reset="handleReset" />

    <div class="table-card" v-loading="loading">
      <div v-if="error" class="error-placeholder">
        <p>数据加载失败，请稍后重试</p>
        <el-button type="primary" @click="fetchLogs" :disabled="retryCooldown">重试</el-button>
      </div>

      <template v-else>
        <LogTable v-if="logs.length > 0" :logs="logs" />
        <el-empty v-else description="暂无登录日志" />

        <LogPagination
          :total="total"
          :skip="skip"
          :limit="limit"
          @change="handlePageChange"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import LogFilter from '../components/logs/LogFilter.vue'
import LogTable from '../components/logs/LogTable.vue'
import LogPagination from '../components/logs/LogPagination.vue'
import { getLogs } from '../api/logs'

const logs = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(50)
const loading = ref(false)
const error = ref(false)
const retryCooldown = ref(false)
let retryTimer = null
const currentFilters = ref({})

const fetchLogs = async () => {
  if (retryCooldown.value) return
  loading.value = true
  error.value = false
  try {
    const res = await getLogs({
      skip: skip.value,
      limit: limit.value,
      ...currentFilters.value
    })
    logs.value = res.items
    total.value = res.total
  } catch (err) {
    console.error('Failed to fetch logs:', err)
    error.value = true
    retryCooldown.value = true
    clearTimeout(retryTimer)
    retryTimer = setTimeout(() => {
      retryCooldown.value = false
    }, 5000)
  } finally {
    loading.value = false
  }
}

const handleSearch = (params) => {
  skip.value = 0
  currentFilters.value = params
  fetchLogs()
}

const handleReset = () => {
  skip.value = 0
  currentFilters.value = {}
  fetchLogs()
}

const handlePageChange = (newSkip, newLimit) => {
  skip.value = newSkip
  limit.value = newLimit
  fetchLogs()
}

onMounted(fetchLogs)

onUnmounted(() => {
  clearTimeout(retryTimer)
  retryTimer = null
})
</script>

<style scoped>
.login-logs-page {
  padding: 0;
}

.table-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 空状态文字颜色与 Caption 层级一致 */
.table-card :deep(.el-empty__description p) {
  color: #9CA3AF;
}

.error-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 0;
}

.error-placeholder p {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}
</style>
