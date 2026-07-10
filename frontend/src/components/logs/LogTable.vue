<template>
  <el-table
    :data="logs"
    class="log-table"
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
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="username" label="用户名" width="90" />
    <el-table-column prop="login_time" label="登录时间" width="150" />
    <el-table-column prop="ip_address" label="IP地址" width="120" />
    <el-table-column prop="login_status" label="状态" width="70" align="center">
      <template #default="{ row }">
        <StatusTag :status="row.login_status" />
      </template>
    </el-table-column>
    <el-table-column label="用户代理" width="320">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.user_agent"
          :content="row.user_agent"
          effect="dark"
          placement="top"
          :show-after="300"
        >
          <span class="ua-text">{{ row.user_agent }}</span>
        </el-tooltip>
        <span v-else class="ua-empty">-</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import StatusTag from '../common/StatusTag.vue'

defineProps({
  logs: {
    type: Array,
    required: true
  }
})

const formatDateTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}
</script>

<style scoped>
.log-table {
  width: 100%;
  overflow-x: auto;
}

/* 用户代理列：截断加省略号 */
.ua-text {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
  vertical-align: middle;
}

.ua-empty {
  color: var(--color-text-tertiary);
}
</style>

<style>
/* 全局样式覆盖 Element Plus 表格 */
.log-table .el-table__body td.el-table__cell .cell {
  white-space: nowrap !important;
  word-break: keep-all !important;
}

.log-table .el-table__header th.el-table__cell .cell {
  white-space: nowrap !important;
  word-break: keep-all !important;
}
</style>