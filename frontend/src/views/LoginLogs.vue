<template>
  <div class="page">
    <LogFilter @search="search" @reset="reset" />

    <SectionCard flush>
      <template #actions>
        <span class="total num">共 {{ total }} 条</span>
        <el-button type="danger" plain :disabled="total === 0" @click="handleClear">
          <el-icon :size="15"><Delete /></el-icon>
          清空日志
        </el-button>
      </template>

      <DataTable
        :items="items"
        :total="total"
        :skip="skip"
        :limit="limit"
        :loading="loading"
        :error="error"
        :cooldown="retryCooldown"
        empty-title="暂无登录日志"
        empty-description="校园系统上报后，登录记录会显示在这里"
        @page-change="changePage"
        @retry="execute"
      >
        <el-table-column prop="id" label="ID" width="72" />
        <el-table-column prop="username" label="用户名" min-width="110" />
        <el-table-column label="登录时间" min-width="160">
          <template #default="{ row }">
            <span class="num">{{ formatDateTime(row.login_time) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" min-width="130">
          <template #default="{ row }">
            <span class="num">{{ row.ip_address }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <StatusTag :status="row.login_status" type="login" />
          </template>
        </el-table-column>
        <el-table-column prop="location" label="地点" min-width="100">
          <template #default="{ row }">
            <span v-if="row.location">{{ row.location }}</span>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="用户代理" min-width="220">
          <template #default="{ row }">
            <el-tooltip
              v-if="row.user_agent"
              :content="row.user_agent"
              effect="dark"
              placement="top"
              :show-after="300"
            >
              <span class="truncate">{{ row.user_agent }}</span>
            </el-tooltip>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
      </DataTable>
    </SectionCard>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { getLogs, clearLogs } from '../api/logs'
import { useTableQuery } from '../composables/useTableQuery'
import { formatDateTime } from '../utils/format'
import SectionCard from '../components/common/SectionCard.vue'
import DataTable from '../components/common/DataTable.vue'
import StatusTag from '../components/common/StatusTag.vue'
import LogFilter from '../components/logs/LogFilter.vue'

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
} = useTableQuery(getLogs, { limit: 20 })

onMounted(execute)

async function handleClear() {
  try {
    await ElMessageBox.confirm(
      '将清空全部登录日志，此操作不可恢复。',
      '确认清空',
      {
        confirmButtonText: '确定清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
    const res = await clearLogs()
    ElMessage.success(`已清空 ${res.deleted} 条日志`)
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

.truncate {
  display: inline-block;
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.muted {
  color: var(--text-faint);
}
</style>
