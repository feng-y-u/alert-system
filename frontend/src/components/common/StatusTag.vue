<template>
  <span class="status-tag" :class="statusClass">
    {{ label }}
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
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.status-success {
  background-color: #d1fae5;
  color: #10b981;
}

.status-failure {
  background-color: #fee2e2;
  color: #ef4444;
}
</style>