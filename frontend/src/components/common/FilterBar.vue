<template>
  <div class="filter-bar">
    <div class="filter-bar__fields">
      <slot />
    </div>
    <div class="filter-bar__actions">
      <el-button type="primary" @click="emit('search')">
        <el-icon><Search /></el-icon>
        查询
      </el-button>
      <el-button @click="emit('reset')">
        <el-icon><RefreshLeft /></el-icon>
        重置
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { RefreshLeft, Search } from '@element-plus/icons-vue'

const emit = defineEmits(['search', 'reset'])
</script>

<style scoped>
.filter-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
  background: var(--bg-surface);
  border-radius: var(--r-lg);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
}

.filter-bar__fields {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  flex: 1;
}

.filter-bar__actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

/* 筛选项统一宽度，由使用方通过 class 覆盖 */
.filter-bar :deep(.filter-field) {
  width: 170px;
}

.filter-bar :deep(.filter-field--wide) {
  width: 270px;
}

.filter-bar :deep(.filter-field--narrow) {
  width: 130px;
}
</style>
