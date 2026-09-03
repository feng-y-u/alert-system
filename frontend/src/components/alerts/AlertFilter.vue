<template>
  <FilterBar @search="handleSearch" @reset="handleReset">
    <el-select
      v-model="filters.status"
      placeholder="告警状态"
      clearable
      class="filter-field filter-field--narrow"
    >
      <el-option label="待处理" value="pending" />
      <el-option label="已确认" value="acknowledged" />
      <el-option label="已处理" value="resolved" />
    </el-select>
    <el-select
      v-model="filters.severity"
      placeholder="严重级别"
      clearable
      class="filter-field filter-field--narrow"
    >
      <el-option label="低" value="low" />
      <el-option label="中" value="medium" />
      <el-option label="高" value="high" />
    </el-select>
    <el-input
      v-model="filters.username"
      placeholder="用户名"
      clearable
      class="filter-field"
    />
  </FilterBar>
</template>

<script setup>
import { reactive } from 'vue'
import FilterBar from '../common/FilterBar.vue'

const emit = defineEmits(['search', 'reset'])

const filters = reactive({
  status: '',
  severity: '',
  username: '',
})

function handleSearch() {
  emit('search', {
    status: filters.status || undefined,
    severity: filters.severity || undefined,
    username: filters.username || undefined,
  })
}

function handleReset() {
  filters.status = ''
  filters.severity = ''
  filters.username = ''
  emit('reset')
}
</script>
