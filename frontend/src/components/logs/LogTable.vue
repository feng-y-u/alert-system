<template>
  <el-table :data="logs" class="log-table">
    <el-table-column prop="username" label="用户名" min-width="120" />
    <el-table-column prop="login_time" label="登录时间" min-width="160">
      <template #default="{ row }">
        {{ formatDateTime(row.login_time) }}
      </template>
    </el-table-column>
    <el-table-column prop="ip_address" label="IP地址" min-width="140" />
    <el-table-column prop="login_status" label="状态" width="80" align="center">
      <template #default="{ row }">
        <StatusTag :status="row.login_status" />
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
}
</style>