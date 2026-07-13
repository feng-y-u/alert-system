<template>
  <div class="filter-card">
    <div class="filter-row">
      <el-select
        v-model="filters.status"
        placeholder="告警状态"
        clearable
        class="filter-item filter-select"
      >
        <el-option label="待处理" value="pending" />
        <el-option label="已确认" value="acknowledged" />
        <el-option label="已处理" value="resolved" />
      </el-select>
      <el-select
        v-model="filters.severity"
        placeholder="严重级别"
        clearable
        class="filter-item filter-select"
      >
        <el-option label="低" value="low" />
        <el-option label="中" value="medium" />
        <el-option label="高" value="high" />
      </el-select>
      <el-input
        v-model="filters.username"
        placeholder="用户名"
        clearable
        class="filter-item"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>
        查询
      </el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { Search } from '@element-plus/icons-vue'

const emit = defineEmits(['search', 'reset'])

const filters = reactive({
  status: '',
  severity: '',
  username: ''
})

const handleSearch = () => {
  const params = {
    status: filters.status || undefined,
    severity: filters.severity || undefined,
    username: filters.username || undefined
  }
  emit('search', params)
}

const handleReset = () => {
  filters.status = ''
  filters.severity = ''
  filters.username = ''
  emit('reset')
}
</script>

<style scoped>
.filter-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-item {
  width: 160px;
}

.filter-select {
  width: 140px;
}
</style>
