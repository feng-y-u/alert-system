<template>
  <div class="login-logs-page">
    <LogFilter @search="handleSearch" @reset="handleReset" />

    <div class="table-card" v-loading="loading">
      <LogTable v-if="logs.length > 0" :logs="logs" />
      <el-empty v-else description="暂无登录日志" />

      <LogPagination
        :total="total"
        :skip="skip"
        :limit="limit"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LogFilter from '../components/logs/LogFilter.vue'
import LogTable from '../components/logs/LogTable.vue'
import LogPagination from '../components/logs/LogPagination.vue'
import { getLogs } from '../api/logs'

const logs = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(50)
const loading = ref(false)
const currentFilters = ref({})

const fetchLogs = async () => {
  loading.value = true
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
    logs.value = []
    total.value = 0
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
</style>
