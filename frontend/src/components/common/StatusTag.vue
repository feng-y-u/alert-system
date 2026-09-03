<template>
  <span class="status-tag" :class="toneClass">
    <span v-if="dot" class="status-tag__dot" />
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  type: {
    type: String,
    default: 'login',
    validator: (v) =>
      ['login', 'alert_status', 'alert_severity', 'alert_type'].includes(v),
  },
  /** 待处理/高危这类需要强调的状态带一个圆点，视觉上更跳 */
  dot: { type: Boolean, default: false },
})

// 后端存的是裸字符串，没有 enum 约束，这里是唯一的展示映射表
const LABELS = {
  login: { success: '成功', failure: '失败' },
  alert_status: { pending: '待处理', acknowledged: '已确认', resolved: '已处理' },
  alert_severity: { low: '低', medium: '中', high: '高' },
  alert_type: { frequency: '频率异常', device: '设备异常' },
}

const TONES = {
  login: { success: 'success', failure: 'danger' },
  alert_status: {
    pending: 'warning',
    acknowledged: 'info',
    resolved: 'success',
  },
  alert_severity: { low: 'info', medium: 'warning', high: 'danger' },
  alert_type: { frequency: 'brand', device: 'neutral' },
}

const label = computed(() => LABELS[props.type]?.[props.status] ?? props.status)
const toneClass = computed(
  () => `status-tag--${TONES[props.type]?.[props.status] ?? 'neutral'}`,
)
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 11px;
  border-radius: var(--r-full);
  font-size: 12px;
  font-weight: 600;
  line-height: 1.5;
  white-space: nowrap;
  letter-spacing: 0.01em;
}

.status-tag__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}

.status-tag--success {
  background: var(--success-soft);
  color: var(--success-ink);
}

.status-tag--danger {
  background: var(--danger-soft);
  color: var(--danger-ink);
}

.status-tag--warning {
  background: var(--warning-soft);
  color: var(--warning-ink);
}

.status-tag--info {
  background: var(--info-soft);
  color: var(--info-ink);
}

.status-tag--brand {
  background: var(--brand-50);
  color: var(--brand-600);
}

.status-tag--neutral {
  background: var(--bg-hover);
  color: var(--text-muted);
}
</style>
