<template>
  <div class="stat-card" :class="`stat-card--${tone}`">
    <div class="stat-card__top">
      <span class="stat-card__label">{{ label }}</span>
      <span class="stat-card__badge">
        <el-icon :size="19"><component :is="icon" /></el-icon>
      </span>
    </div>
    <div class="stat-card__value num">{{ displayValue }}</div>
    <div v-if="hint" class="stat-card__hint">{{ hint }}</div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { TrendCharts } from '@element-plus/icons-vue'
import { formatNumber } from '../../utils/format'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: [String, Object], default: () => TrendCharts },
  tone: { type: String, default: 'brand' },
  hint: { type: String, default: '' },
})

const REDUCED_MOTION =
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const isNumber = computed(() => typeof props.value === 'number')
const animatedNumber = ref(0)
let rafId = null

function cancelAnimation() {
  if (rafId !== null) {
    cancelAnimationFrame(rafId)
    rafId = null
  }
}

/**
 * 数字滚动：从当前显示值平滑滚动到目标值。
 * 首屏挂载时从 0 滚到统计值；数值变化（如刷新）时从旧值滚到新值。
 */
function animateTo(target) {
  if (typeof target !== 'number') return
  if (REDUCED_MOTION) {
    animatedNumber.value = target
    return
  }
  cancelAnimation()
  const from = animatedNumber.value
  const delta = target - from
  if (delta === 0) return

  const duration = 900
  const startAt = performance.now()
  const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3)

  const step = (now) => {
    const progress = Math.min((now - startAt) / duration, 1)
    animatedNumber.value = Math.round(from + delta * easeOutCubic(progress))
    if (progress < 1) {
      rafId = requestAnimationFrame(step)
    } else {
      rafId = null
    }
  }
  rafId = requestAnimationFrame(step)
}

watch(() => props.value, (v) => animateTo(v), { immediate: true })
onBeforeUnmount(cancelAnimation)

const displayValue = computed(() =>
  isNumber.value ? formatNumber(animatedNumber.value) : props.value,
)
</script>

<style scoped>
.stat-card {
  position: relative;
  background: var(--bg-surface);
  border-radius: var(--r-lg);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  transition: box-shadow var(--dur) var(--ease), transform var(--dur) var(--ease);
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* 右上角的柔和色晕，增加层次而不抢眼 */
.stat-card::after {
  content: '';
  position: absolute;
  top: -40px;
  right: -40px;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: var(--tone-soft);
  opacity: 0.55;
  pointer-events: none;
}

.stat-card--brand {
  --tone-soft: var(--brand-50);
  --tone-ink: var(--brand-600);
}

.stat-card--warning {
  --tone-soft: var(--warning-soft);
  --tone-ink: var(--warning-ink);
}

.stat-card--success {
  --tone-soft: var(--success-soft);
  --tone-ink: var(--success-ink);
}

.stat-card--info {
  --tone-soft: var(--info-soft);
  --tone-ink: var(--info-ink);
}

.stat-card__top {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.stat-card__label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}

.stat-card__badge {
  width: 40px;
  height: 40px;
  border-radius: var(--r-md);
  background: var(--tone-soft);
  color: var(--tone-ink);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-card__value {
  position: relative;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.15;
  color: var(--text-strong);
  letter-spacing: -0.02em;
}

.stat-card__hint {
  position: relative;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-faint);
}
</style>
