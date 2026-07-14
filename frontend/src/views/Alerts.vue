<template>
  <div class="alerts-page">
    <AlertFilter @search="handleSearch" @reset="handleReset" />

    <div class="table-card" v-loading="loading">
      <div v-if="error" class="error-placeholder">
        <p>数据加载失败，请稍后重试</p>
        <el-button type="primary" @click="fetchAlerts">重试</el-button>
      </div>

      <template v-else>
        <AlertTable
          v-if="alerts.length > 0"
          :alerts="alerts"
          @status-change="handleStatusChange"
        />
        <el-empty v-else description="暂无告警" />

        <AlertPagination
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
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AlertFilter from '../components/alerts/AlertFilter.vue'
import AlertTable from '../components/alerts/AlertTable.vue'
import AlertPagination from '../components/alerts/AlertPagination.vue'
import { getAlerts, updateAlertStatus } from '../api/alerts'
import { useNotificationStore } from '../stores/notification'

const notificationStore = useNotificationStore()

const alerts = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(50)
const loading = ref(false)
const error = ref(false)
const currentFilters = ref({})

const fetchAlerts = async () => {
  loading.value = true
  error.value = false
  try {
    const res = await getAlerts({
      skip: skip.value,
      limit: limit.value,
      ...currentFilters.value
    })
    alerts.value = res.items
    total.value = res.total
  } catch (err) {
    console.error('Failed to fetch alerts:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const handleSearch = (params) => {
  skip.value = 0
  currentFilters.value = params
  fetchAlerts()
}

const handleReset = () => {
  skip.value = 0
  currentFilters.value = {}
  fetchAlerts()
}

const handlePageChange = (newSkip, newLimit) => {
  skip.value = newSkip
  limit.value = newLimit
  fetchAlerts()
}

const handleStatusChange = async (alertId, newStatus) => {
  try {
    await updateAlertStatus(alertId, newStatus)
    ElMessage.success('告警状态已更新')
    fetchAlerts()
  } catch (err) {
    console.error('Failed to update alert status:', err)
    ElMessage.error('更新告警状态失败')
  }
}

onMounted(() => {
  fetchAlerts()
  notificationStore.clearUnread()
})
</script>

<style scoped>
.alerts-page {
  padding: 0;
}

.table-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

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
