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
      borderBottomColor: 'var(--color-border-light)'
    }"
  >
    <el-table-column prop="id" label="ID" width="80" />
    <el-table-column prop="username" label="用户名" min-width="120" />
    <el-table-column prop="login_status" label="状态" width="80" align="left">
      <template #default="{ row }">
        <StatusTag :status="row.login_status" />
      </template>
    </el-table-column>
    <el-table-column prop="login_time" label="登录时间" width="170">
      <template #default="{ row }">
        {{ formatDateTime(row.login_time) }}
      </template>
    </el-table-column>
    <el-table-column prop="ip_address" label="IP地址" width="140" />
    <el-table-column label="用户代理" min-width="200" flex="1">
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

/* 所有数据单元格不换行 */
.log-table :deep(.el-table__body td.el-table__cell) {
  white-space: nowrap;
}

/* 用户代理列：截断加省略号 */
.ua-text {
  display: block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}

.ua-empty {
  color: var(--color-text-tertiary);
}
</style>