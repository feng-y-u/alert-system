<template>
  <div class="alerts-page">
    <AlertFilter @search="handleSearch" @reset="handleReset" />

    <div class="toolbar">
      <div class="toolbar-left">
        <span class="total-label">共 {{ total }} 条告警</span>
      </div>
      <div class="toolbar-right">
        <el-dropdown trigger="click" @command="handleClear">
          <el-button type="danger" plain :disabled="total === 0">
            <el-icon :size="16"><Delete /></el-icon>
            清空
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="all">清空全部</el-dropdown-item>
              <el-dropdown-item command="processed">清空已处理</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <div class="table-card" v-loading="loading">
      <div v-if="error" class="error-placeholder">
        <p>数据加载失败，请稍后重试</p>
        <el-button type="primary" @click="fetchAlerts" :disabled="retryCooldown">重试</el-button>
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
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import AlertFilter from '../components/alerts/AlertFilter.vue'
import AlertTable from '../components/alerts/AlertTable.vue'
import AlertPagination from '../components/alerts/AlertPagination.vue'
import { getAlerts, updateAlertStatus, clearAlerts } from '../api/alerts'
import { useNotificationStore } from '../stores/notification'

const notificationStore = useNotificationStore()

const alerts = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(50)
const loading = ref(false)
const error = ref(false)
const retryCooldown = ref(false)
let retryTimer = null
const currentFilters = ref({})

const fetchAlerts = async () => {
  if (retryCooldown.value) return
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

const handleClear = async (scope) => {
  const label = scope === 'all' ? '全部' : '已处理'
  try {
    await ElMessageBox.confirm(
      `确定清空${label}告警？此操作不可恢复。`,
      '确认清空',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    const res = await clearAlerts(scope)
    ElMessage.success(`已清空 ${res.deleted} 条${label}告警`)
    skip.value = 0
    fetchAlerts()
  } catch {
    // 取消或失败都不处理
  }
}

onMounted(() => {
  fetchAlerts()
  notificationStore.clearUnread()
})

onUnmounted(() => {
  clearTimeout(retryTimer)
  retryTimer = null
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

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.total-label {
  font-size: 14px;
  color: var(--color-text-secondary);
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
