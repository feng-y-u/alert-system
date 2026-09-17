<template>
  <div
    ref="container"
    class="base-chart"
    :class="{ 'is-swapping': swapping }"
    :style="{ height }"
  />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

import { useReducedMotion } from '../../composables/useReducedMotion'
import { isSameCategories } from '../../utils/chart'
import { DURATION, easeOutCubic } from '../../utils/motion'

const props = defineProps({
  /** 完整的 ECharts option，由各图表组件负责构造 */
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
  /**
   * 首屏入场方式（仅首次渲染）：
   * - none（默认）：交给 ECharts 自身的入场动画
   * - sweep：让折线按数据点顺序从左到右逐点绘制（仅适合折线图）
   */
  entrance: { type: String, default: 'none' },
})

const container = ref(null)
const reduced = useReducedMotion()
/** 换数据期间的整图压暗（CSS 过渡，见 style） */
const swapping = ref(false)

let chart = null
let observer = null
let resizeRaf = null
let sweepRaf = null
let swapTimer = null
let hasRendered = false

/** 图表**当前已呈现**的 option，用于判定下一次更新属于哪一类 */
let shownOption = null
/** 切换在途时的最新目标 option：只保留最后一个，绝不排队堆积 */
let pendingOption = null

/**
 * 换数据的时机：等淡出结束。
 * CSS 淡出用 --motion-fast（140ms），这里留 20ms 余量。
 */
const SWAP_AT_MS = DURATION.fast + 20

/** 合并渲染：保留系列实例，让数值型更新走 update 过渡而不是重建 */
const MERGE = { notMerge: false, lazyUpdate: true }

/** 关掉所有补间：轴、曲线、面积、Y 范围在同一帧内整体替换 */
function withoutTween(option) {
  return {
    ...option,
    animation: false,
    animationDuration: 0,
    animationDurationUpdate: 0,
  }
}

function disposeSweep() {
  if (sweepRaf !== null) {
    cancelAnimationFrame(sweepRaf)
    sweepRaf = null
  }
}

function cancelSwapTimer() {
  if (swapTimer !== null) {
    clearTimeout(swapTimer)
    swapTimer = null
  }
}

/**
 * X 轴类目变化（7 天 ↔ 30 天）时的换数据流程：
 *
 *   淡出（CSS 140ms）→ 关掉补间、原子替换整份数据 → 淡入（CSS 220ms）
 *
 * 关键点：替换发生在**同一帧**内，且期间不产生任何跨类目补间，
 * 因此不存在「旧曲线 + 新曲线同时可见」，也不存在两套数据的中间形态。
 */
function requestSwap(option) {
  pendingOption = option
  // 已有切换在途：只替换目标，不重新计时、不排队 —— 连续快速点击只会落到最后一帧
  if (swapTimer !== null) return

  swapping.value = true
  swapTimer = setTimeout(() => {
    swapTimer = null
    const next = pendingOption
    pendingOption = null
    if (chart && next) {
      chart.setOption(withoutTween(next), { notMerge: false, lazyUpdate: false })
    }
    swapping.value = false
  }, SWAP_AT_MS)
}

/** 构造「只显示前 count 个点」的 option，用于首屏逐点绘制 */
function optionWithPoints(option, count) {
  if (!Array.isArray(option.series)) return option
  return {
    ...withoutTween(option),
    series: option.series.map((series) =>
      Array.isArray(series.data)
        ? { ...series, data: series.data.slice(0, count) }
        : series,
    ),
  }
}

/** 从左到右逐点绘制折线（仅首屏，且尊重减少动态效果偏好） */
function runSweep(option) {
  const firstSeries = Array.isArray(option.series) ? option.series[0] : null
  const total = Array.isArray(firstSeries?.data) ? firstSeries.data.length : 0

  if (total < 3 || reduced.value) {
    chart.setOption(option, MERGE)
    return
  }

  const startedAt = performance.now()
  const duration = DURATION.chartLine

  const step = (now) => {
    const progress = Math.min((now - startedAt) / duration, 1)
    const count = Math.max(1, Math.ceil(easeOutCubic(progress) * total))
    chart.setOption(optionWithPoints(option, count), MERGE)
    if (progress < 1) {
      sweepRaf = requestAnimationFrame(step)
    } else {
      sweepRaf = null
      // 收尾渲染完整 option（此时已是同一份数据，不会二次跳动）
      chart.setOption(option, MERGE)
    }
  }

  sweepRaf = requestAnimationFrame(step)
}

function render() {
  if (!container.value) return
  if (!chart) chart = echarts.init(container.value)

  const option = props.option

  // ── 首屏：一次性入场 ─────────────────────────────────────
  if (!hasRendered) {
    hasRendered = true
    shownOption = option
    if (props.entrance === 'sweep' && !reduced.value) {
      runSweep(option)
      return
    }
    chart.setOption(option, MERGE)
    return
  }

  disposeSweep()

  // ── 切换在途：并入最新目标，避免打断淡出流程 ─────────────
  if (swapTimer !== null) {
    shownOption = option
    requestSwap(option)
    return
  }

  // ── 类目一致（同一时间窗内数值刷新）：点对点形变，最自然 ──
  if (isSameCategories(shownOption, option)) {
    shownOption = option
    chart.setOption(option, MERGE)
    return
  }

  // ── 类目变化（7 天 ↔ 30 天）：原子替换，绝不跨类目形变 ────
  shownOption = option
  if (reduced.value) {
    chart.setOption(withoutTween(option), { notMerge: false, lazyUpdate: false })
    return
  }
  requestSwap(option)
}

/**
 * resize 用 rAF 合并：侧边栏折叠是 220ms 的宽度过渡，
 * ResizeObserver 会连续触发，逐次 resize 会让多个画布在同一帧内反复重排。
 */
function scheduleResize() {
  if (resizeRaf !== null) return
  resizeRaf = requestAnimationFrame(() => {
    resizeRaf = null
    chart?.resize()
  })
}

onMounted(() => {
  render()
  observer = new ResizeObserver(scheduleResize)
  observer.observe(container.value)
})

// 各图表组件的 option 都是 computed 新建的对象，浅比较即可；
// 去掉 deep:true 避免每次变化都对整棵 option 树做深度遍历
watch(() => props.option, () => render())

// 运行中切换「减少动态效果」：立刻停下逐点绘制与换数据过渡，直接落到终态
watch(reduced, (isReduced) => {
  if (!isReduced) return
  disposeSweep()
  cancelSwapTimer()
  pendingOption = null
  swapping.value = false
  if (chart && props.option) {
    chart.setOption(withoutTween(props.option), { notMerge: false, lazyUpdate: false })
  }
})

onBeforeUnmount(() => {
  disposeSweep()
  cancelSwapTimer()
  pendingOption = null
  if (resizeRaf !== null) {
    cancelAnimationFrame(resizeRaf)
    resizeRaf = null
  }
  observer?.disconnect()
  observer = null
  chart?.dispose()
  chart = null
})
</script>

<style scoped>
.base-chart {
  width: 100%;
  /* 淡入较慢（220ms）、淡出更快（140ms）：
     换数据发生在淡出结束处，此时新旧数据不同时可见 */
  transition: opacity var(--motion-base, 220ms) var(--ease-standard, ease);
}

.base-chart.is-swapping {
  opacity: 0.25;
  transition-duration: var(--motion-fast, 140ms);
}
</style>
