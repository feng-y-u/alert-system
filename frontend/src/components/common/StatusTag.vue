<template>
  <span class="status-tag" :class="statusClass">
    <span class="status-bar" :class="statusClass"></span>
    <span class="status-text">{{ label }}</span>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusClass = computed(() => ({
  'status-success': props.status === 'success',
  'status-failure': props.status === 'failure'
}))

const label = computed(() => ({
  success: '成功',
  failure: '失败'
}[props.status] || props.status))
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 4px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: transparent;
}

.status-bar {
  width: 3px;
  height: 14px;
  border-radius: 2px;
  flex-shrink: 0;
}

.status-text {
  line-height: 20px;
}

.status-success .status-bar {
  background-color: #10b981;
}

.status-success .status-text {
  color: #10b981;
}

.status-failure .status-bar {
  background-color: #ef4444;
}

.status-failure .status-text {
  color: #ef4444;
}
</style>