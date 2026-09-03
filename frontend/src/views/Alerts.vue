<template>
  <div class="page">
    <AlertFilter @search="search" @reset="reset" />

    <SectionCard flush>
      <template #actions>
        <span class="total num">共 {{ total }} 条</span>
        <el-dropdown trigger="click" @command="handleClear">
          <el-button type="danger" plain :disabled="total === 0">
            <el-icon :size="15"><Delete /></el-icon>
            清空告警
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="all">清空全部</el-dropdown-item>
              <el-dropdown-item command="processed">清空已处理</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>

      <DataTable
        :items="items"
        :total="total"
        :skip="skip"
        :limit="limit"
        :loading="loading"
        :error="error"
        :cooldown="retryCooldown"
        empty-title="暂无告警"
        empty-description="未检测到异常登录行为"
        @page-change="changePage"
        @retry="execute"
      >
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="username" label="用户名" min-width="110" />
        <el-table-column label="类型" width="110">
          <template #default="{ row }">
            <StatusTag :status="row.alert_type" type="alert_type" />
          </template>
        </el-table-column>
        <el-table-column label="级别" width="90" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.severity"
              type="alert_severity"
              :dot="row.severity === 'high'"
            />
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <StatusTag
              :status="row.status"
              type="alert_status"
              :dot="row.status === 'pending'"
            />
          </template>
        </el-table-column>
        <el-table-column label="告警内容" min-width="240">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.alert_message"
              :content="row.alert_message"
              effect="dark"
              placement="top"
              :show-after="300"
            >
              <span class="truncate">{{ row.alert_message }}</span>
            </el-tooltip>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="160">
          <template #default="{ row }">
            <span class="num">{{ formatDateTime(row.created_at) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-dropdown
              trigger="click"
              @command="(cmd) => handleStatusChange(row.id, cmd)"
            >
              <button class="row-action" aria-label="更多操作">
                <el-icon :size="16"><MoreFilled /></el-icon>
              </button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    v-for="opt in STATUS_OPTIONS"
                    :key="opt.value"
                    :command="opt.value"
                    :disabled="row.status === opt.value"
                  >
                    {{ opt.label }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </DataTable>
    </SectionCard>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, MoreFilled } from '@element-plus/icons-vue'
import { clearAlerts, getAlerts, updateAlertStatus } from '../api/alerts'
import { useNotificationStore } from '../stores/notification'
import { useTableQuery } from '../composables/useTableQuery'
import { formatDateTime } from '../utils/format'
import SectionCard from '../components/common/SectionCard.vue'
import DataTable from '../components/common/DataTable.vue'
import StatusTag from '../components/common/StatusTag.vue'
import AlertFilter from '../components/alerts/AlertFilter.vue'

const STATUS_OPTIONS = [
  { value: 'pending', label: '标记为待处理' },
  { value: 'acknowledged', label: '标记为已确认' },
  { value: 'resolved', label: '标记为已处理' },
]

const notificationStore = useNotificationStore()

const {
  items,
  total,
  skip,
  limit,
  loading,
  error,
  retryCooldown,
  search,
  reset,
  changePage,
  refresh,
  execute,
} = useTableQuery(getAlerts, { limit: 20 })

onMounted(() => {
  execute()
  // 进入告警页即视为已读
  notificationStore.clearUnread()
})

async function handleStatusChange(alertId, status) {
  try {
    await updateAlertStatus(alertId, status)
    ElMessage.success('告警状态已更新')
    refresh()
  } catch {
    ElMessage.error('更新告警状态失败')
  }
}

async function handleClear(scope) {
  const label = scope === 'all' ? '全部' : '已处理'
  try {
    await ElMessageBox.confirm(
      `将清空${label}告警，此操作不可恢复。`,
      '确认清空',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
    const res = await clearAlerts(scope)
    ElMessage.success(`已清空 ${res.deleted} 条${label}告警`)
    skip.value = 0
    refresh()
  } catch {
    // 用户取消或删除失败，均不处理
  }
}
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.total {
  font-size: 13px;
  color: var(--text-muted);
  margin-right: 4px;
}

.row-action {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  color: var(--text-faint);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--dur) var(--ease);
}

.row-action:hover {
  background: var(--bg-hover);
  color: var(--text-strong);
}

.truncate {
  display: inline-block;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.muted {
  color: var(--text-faint);
}
</style>
