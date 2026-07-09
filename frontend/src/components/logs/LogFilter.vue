<template>
  <div class="filter-card">
    <div class="filter-row">
      <el-input
        v-model="filters.username"
        placeholder="用户名"
        clearable
        class="filter-input"
      />
      <el-input
        v-model="filters.ip_address"
        placeholder="IP地址"
        clearable
        class="filter-input"
      />
      <el-select
        v-model="filters.login_status"
        placeholder="登录状态"
        clearable
        class="filter-select"
      >
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failure" />
      </el-select>
      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        class="filter-date"
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
  username: '',
  ip_address: '',
  login_status: '',
  dateRange: null
})

const handleSearch = () => {
  const params = {
    username: filters.username || undefined,
    ip_address: filters.ip_address || undefined,
    login_status: filters.login_status || undefined,
    start_time: filters.dateRange?.[0] ? `${filters.dateRange[0]}T00:00:00` : undefined,
    end_time: filters.dateRange?.[1] ? `${filters.dateRange[1]}T23:59:59` : undefined
  }
  emit('search', params)
}

const handleReset = () => {
  filters.username = ''
  filters.ip_address = ''
  filters.login_status = ''
  filters.dateRange = null
  emit('reset')
}
</script>

<style scoped>
.filter-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
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

.filter-input {
  width: 160px;
}

.filter-select {
  width: 140px;
}

.filter-date {
  width: 280px;
}
</style>