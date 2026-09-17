<template>
  <div class="stat-card" :class="[`stat-card--${tone}`, { 'is-alert': isAlert, 'is-changed': justChanged }]">
    <div class="stat-card__top">
      <span class="stat-card__label">{{ label }}</span>
      <span class="stat-card__badge">
        <el-icon :size="19"><component :is="icon" /></el-icon>
      </span>
    </div>

    <div class="stat-card__value">
      <!-- 数据未到位时给骨架而不是先显示 0：避免"先看到 0 再跳数"的廉价感 -->
      <span v-if="!ready" class="stat-card__skeleton" aria-hidden="true" />
      <span v-else class="stat-card__number num">{{ display }}</span>
    </div>

    <div v-if="hint" class="stat-card__hint">{{ hint }}</div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { TrendCharts } from '@element-plus/icons-vue'

import { useCountUp } from '../../composables/useCountUp'
import { formatNumber } from '../../utils/format'

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [Number, String], default: 0 },
  icon: { type: [String, Object], default: () => TrendCharts },
  tone: { type: String, default: 'brand' },
  hint: { type: String, default: '' },
  /** 数据是否已就绪：未就绪显示骨架，就绪后数字才平滑滚入 */
  ready: { type: Boolean, default: true },
})

const isNumber = computed(() => typeof props.value === 'number')
const numericValue = computed(() => (isNumber.value ? props.value : 0))

const { display } = useCountUp(numericValue, { format: formatNumber })

/** 告警态：只有 warning 语气 + 有值时才是"需要注意"，避免常亮造成疲劳 */
const isAlert = computed(() => props.tone === 'warning' && numericValue.value > 0)

/**
 * 数值变化后的短暂高亮：让用户能感知"这次刷新数据变了"。
 * 只在已经渲染过一次之后触发，首屏不闪。
 */
const justChanged = ref(false)
let changedTimer = null
let seenFirstValue = false

watch(numericValue, () => {
  if (!seenFirstValue) {
    seenFirstValue = true
    return
  }
  justChanged.value = true
  clearTimeout(changedTimer)
  changedTimer = setTimeout(() => {
    justChanged.value = false
  }, 1200)
})

onBeforeUnmount(() => clearTimeout(changedTimer))
</script>

<style scoped>
.stat-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid transparent;
  border-radius: var(--r-lg);
  padding: 22px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  /* 只过渡绘制类属性，避免布局回流；时长与曲线来自统一动效令牌 */
  transition:
    transform var(--motion-fast) var(--ease-standard),
    box-shadow var(--motion-fast) var(--ease-standard),
    border-color var(--motion-fast) var(--ease-standard);
}

/* hover：位移 1px + 阴影加深 + 语气色描边。刻意不做缩放，避免"跳动" */
.stat-card:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
  border-color: var(--border);
}

.stat-card.is-alert {
  border-color: var(--warning-soft);
}

/* 告警态左侧强调条：静态、明确，不参与动画 */
.stat-card.is-alert::before {
  content: '';
  position: absolute;
  left: 0;
  top: 18px;
  bottom: 18px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--warning-ink);
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
  transition: opacity var(--motion-base) var(--ease-standard);
}

.stat-card:hover::after {
  opacity: 0.75;
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
  transition: background-color var(--motion-fast) var(--ease-standard);
}

.stat-card:hover .stat-card__badge {
  background: var(--tone-soft);
  filter: saturate(1.1);
}

/* 告警态：徽标做一次性强调（2 次），不是常驻闪烁 */
.stat-card.is-alert .stat-card__badge {
  animation: stat-badge-nudge 900ms var(--ease-standard) 1 2;
}

@keyframes stat-badge-nudge {
  0%,
  100% {
    box-shadow: 0 0 0 0 var(--warning-soft);
  }
  45% {
    box-shadow: 0 0 0 6px var(--warning-soft);
  }
}

.stat-card__value {
  position: relative;
  display: flex;
  align-items: center;
  min-height: 40px;
  font-size: 34px;
  font-weight: 700;
  line-height: 1.15;
  color: var(--text-strong);
  letter-spacing: -0.02em;
}

/* 等宽数字：数值滚动时字宽不变，避免周边元素被推挤 */
.stat-card__number {
  font-variant-numeric: tabular-nums;
  transition: color var(--motion-slow) var(--ease-standard);
}

.stat-card.is-changed .stat-card__number {
  color: var(--brand-600);
}

.stat-card__skeleton {
  display: block;
  width: 96px;
  height: 22px;
  border-radius: 6px;
  background: linear-gradient(
    90deg,
    var(--bg-subtle) 0%,
    var(--bg-hover) 40%,
    var(--bg-subtle) 80%
  );
  background-size: 220% 100%;
  animation: stat-skeleton 1.6s var(--ease-standard) infinite;
}

@keyframes stat-skeleton {
  from {
    background-position: 120% 0;
  }
  to {
    background-position: -60% 0;
  }
}

.stat-card__hint {
  position: relative;
  margin-top: 10px;
  font-size: 12px;
  color: var(--text-faint);
}

@media (prefers-reduced-motion: reduce) {
  .stat-card.is-alert .stat-card__badge {
    animation: none;
  }

  .stat-card__skeleton {
    animation: none;
    background: var(--bg-subtle);
  }
}
</style>
