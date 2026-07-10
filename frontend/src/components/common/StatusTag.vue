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
  'status-tag--success': props.status === 'success',
  'status-tag--failure': props.status === 'failure'
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
  line-height: 1;
}

.status-tag--success {
  background: var(--color-success-light);
  color: var(--color-success);
}

.status-tag--failure {
  background: var(--color-danger-light);
  color: var(--color-danger);
}
</style>