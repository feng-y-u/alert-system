<template>
  <el-table
    :data="alerts"
    class="alert-table"
    stripe
    :header-cell-style="() => ({
      backgroundColor: 'var(--color-bg)',
      color: 'var(--color-text-secondary)',
      fontWeight: 600,
      fontSize: '12px',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      borderBottomColor: 'var(--color-border)',
      whiteSpace: 'nowrap',
    })"
    :cell-style="{
      borderBottomColor: 'var(--color-border-light)',
      whiteSpace: 'nowrap'
    }"
  >
    <el-table-column prop="id" label="ID" min-width="60" />
    <el-table-column prop="username" label="用户名" min-width="100" />
    <el-table-column label="类型" min-width="100">
      <template #default="{ row }">
        <StatusTag :status="row.alert_type" type="alert_type" />
      </template>
    </el-table-column>
    <el-table-column label="级别" min-width="80" align="center">
      <template #default="{ row }">
        <StatusTag :status="row.severity" type="alert_severity" />
      </template>
    </el-table-column>
    <el-table-column label="状态" min-width="100" align="center">
      <template #default="{ row }">
        <StatusTag :status="row.status" type="alert_status" />
      </template>
    </el-table-column>
    <el-table-column label="告警内容" min-width="200">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.alert_message"
          :content="row.alert_message"
          effect="dark"
          placement="top"
          :show-after="300"
        >
          <span class="msg-text">{{ row.alert_message }}</span>
        </el-tooltip>
        <span v-else class="msg-empty">-</span>
      </template>
    </el-table-column>
    <el-table-column label="创建时间" min-width="150">
      <template #default="{ row }">
        {{ formatDateTime(row.created_at) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" min-width="80" align="center">
      <template #default="{ row }">
        <el-dropdown trigger="click" @command="(cmd) => emit('status-change', row.id, cmd)">
          <el-button text>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pending" :disabled="row.status === 'pending'">
                标记为待处理
              </el-dropdown-item>
              <el-dropdown-item command="acknowledged" :disabled="row.status === 'acknowledged'">
                标记为已确认
              </el-dropdown-item>
              <el-dropdown-item command="resolved" :disabled="row.status === 'resolved'">
                标记为已处理
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { MoreFilled } from '@element-plus/icons-vue'
import StatusTag from '../common/StatusTag.vue'
import { formatDateTime } from '../../utils/format'

defineProps({
  alerts: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['status-change'])
</script>

<style scoped>
.alert-table {
  width: 100%;
  overflow-x: auto;
}

.msg-text {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
  vertical-align: middle;
}

.msg-empty {
  color: var(--color-text-tertiary);
}
</style>

<style>
.alert-table .el-table__body td.el-table__cell .cell,
.alert-table .el-table__header th.el-table__cell .cell {
  white-space: nowrap !important;
  word-break: keep-all !important;
}
</style>
