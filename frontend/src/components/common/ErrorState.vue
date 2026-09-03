<template>
  <div class="error-state">
    <div class="error-icon">
      <el-icon :size="26"><WarningFilled /></el-icon>
    </div>
    <p class="error-title">{{ title }}</p>
    <p v-if="description" class="error-desc">{{ description }}</p>
    <el-button type="primary" :disabled="cooldown" @click="emit('retry')">
      <el-icon><Refresh /></el-icon>
      {{ cooldown ? '请稍候…' : '重试' }}
    </el-button>
  </div>
</template>

<script setup>
import { Refresh, WarningFilled } from '@element-plus/icons-vue'

defineProps({
  title: { type: String, default: '数据加载失败' },
  description: { type: String, default: '请检查网络或服务状态后重试' },
  cooldown: { type: Boolean, default: false },
})

const emit = defineEmits(['retry'])
</script>

<style scoped>
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 60px 24px;
  text-align: center;
}

.error-icon {
  width: 60px;
  height: 60px;
  border-radius: var(--r-lg);
  background: var(--danger-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--danger);
  margin-bottom: 6px;
}

.error-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-strong);
}

.error-desc {
  font-size: 13px;
  color: var(--text-faint);
  margin-bottom: 8px;
}
</style>
