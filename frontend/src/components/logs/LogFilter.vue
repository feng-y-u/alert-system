<template>
  <FilterBar @search="handleSearch" @reset="handleReset">
    <el-input
      v-model="filters.username"
      placeholder="用户名"
      clearable
      class="filter-field"
    />
    <el-input
      v-model="filters.ip_address"
      placeholder="IP 地址"
      clearable
      class="filter-field"
    />
    <el-select
      v-model="filters.login_status"
      placeholder="登录状态"
      clearable
      class="filter-field filter-field--narrow"
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
      class="filter-field filter-field--wide"
    />
  </FilterBar>
</template>

<script setup>
import { reactive } from 'vue'
import FilterBar from '../common/FilterBar.vue'

const emit = defineEmits(['search', 'reset'])

const filters = reactive({
  username: '',
  ip_address: '',
  login_status: '',
  dateRange: null,
})

function handleSearch() {
  emit('search', {
    username: filters.username || undefined,
    ip_address: filters.ip_address || undefined,
    login_status: filters.login_status || undefined,
    // 后端接收的是完整时间戳，日期需补齐起止时刻
    start_time: filters.dateRange?.[0]
      ? `${filters.dateRange[0]}T00:00:00`
      : undefined,
    end_time: filters.dateRange?.[1]
      ? `${filters.dateRange[1]}T23:59:59`
      : undefined,
  })
}

function handleReset() {
  filters.username = ''
  filters.ip_address = ''
  filters.login_status = ''
  filters.dateRange = null
  emit('reset')
}
</script>
