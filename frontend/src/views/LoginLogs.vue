<template>
  <div class="login-logs-page">
    <h1 class="page-title">登录日志</h1>
    
    <LogFilter @search="handleSearch" @reset="handleReset" />
    
    <div class="table-card">
      <LogTable :logs="logs" />
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
const currentFilters = ref({})

const fetchLogs = async () => {
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
  padding: 32px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
}

.table-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}
</style>
