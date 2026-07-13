<template>
  <span class="status-tag" :class="classObj">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'login'
  }
})

const labelMap = {
  login: { success: '成功', failure: '失败' },
  alert_status: { pending: '待处理', acknowledged: '已确认', resolved: '已处理' },
  alert_severity: { low: '低', medium: '中', high: '高' },
  alert_type: { frequency: '频率异常', device: '设备异常' }
}

const classMap = {
  login: { success: 'status-tag--success', failure: 'status-tag--failure' },
  alert_status: {
    pending: 'status-tag--warning',
    acknowledged: 'status-tag--info',
    resolved: 'status-tag--success'
  },
  alert_severity: {
    low: 'status-tag--info',
    medium: 'status-tag--warning',
    high: 'status-tag--failure'
  },
  alert_type: {
    frequency: 'status-tag--neutral',
    device: 'status-tag--neutral'
  }
}

const label = computed(() => labelMap[props.type]?.[props.status] || props.status)
const classObj = computed(() => ({
  [classMap[props.type]?.[props.status] || '']: true
}))
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

.status-tag--warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.status-tag--info {
  background: #dbeafe;
  color: #3b82f6;
}

.status-tag--neutral {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}
</style>
