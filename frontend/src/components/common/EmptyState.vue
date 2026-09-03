<template>
  <div class="empty-state">
    <div class="empty-icon">
      <el-icon :size="26"><component :is="icon" /></el-icon>
    </div>
    <p class="empty-title">{{ title }}</p>
    <p v-if="description" class="empty-desc">{{ description }}</p>
    <slot />
  </div>
</template>

<script setup>
import { Box } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '暂无数据' },
  description: { type: String, default: '' },
  icon: { type: [String, Object], default: () => Box },
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 60px 24px;
  text-align: center;
}

.empty-icon {
  width: 60px;
  height: 60px;
  border-radius: var(--r-lg);
  background: var(--bg-subtle);
  border: 1px solid var(--border-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-faint);
  margin-bottom: 6px;
}

.empty-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-strong);
}

.empty-desc {
  font-size: 13px;
  color: var(--text-faint);
  max-width: 380px;
}
</style>
