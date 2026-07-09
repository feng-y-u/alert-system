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
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
}

.status-success {
  color: #10b981;
}

.status-failure {
  color: #ef4444;
}
</style>