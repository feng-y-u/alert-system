<template>
  <div ref="container" class="base-chart" :style="{ height }" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

import { useReducedMotion } from '../../composables/useReducedMotion'
import { easeOutCubic, DURATION } from '../../utils/motion'

const props = defineProps({
  /** 完整的 ECharts option，由各图表组件负责构造 */
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
  /**
   * 首屏入场方式：
   * - none（默认）：交给 ECharts 自身的入场动画
   * - sweep：让折线按数据点顺序**从左到右逐点绘制**（仅适合折线图）
   *
   * 旧实现用 `notMerge: true` 在每次数据变化时整图重绘来「重放入场」，
   * 结果是切换时间范围时整图闪一下重画。现在入场与更新彻底分开：
   * 入场只发生在首次渲染，更新一律走 `animationDurationUpdate` 的形变过渡。
   */
  entrance: { type: String, default: 'none' },
})

const container = ref(null)
const reduced = useReducedMotion()

let chart = null
let observer = null
let resizeRaf = null
let sweepRaf = null
let hasRendered = false

/** 合并渲染：保留系列实例，让数据变化走 update 过渡而不是重建 */
const MERGE = { notMerge: false, lazyUpdate: true }

function disposeSweep() {
  if (sweepRaf !== null) {
    cancelAnimationFrame(sweepRaf)
    sweepRaf = null
  }
}

/** 构造「只显示前 count 个点」的 option，用于逐点绘制 */
function optionWithPoints(option, count) {
  if (!Array.isArray(option.series)) return option
  return {
    ...option,
    // 逐帧推进时不叠加 ECharts 自身动画，否则每帧都会重新起一次过渡
    animation: false,
    animationDurationUpdate: 0,
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

  if (!hasRendered) {
    hasRendered = true
    if (props.entrance === 'sweep') {
      runSweep(props.option)
      return
    }
  }

  disposeSweep()
  chart.setOption(props.option, MERGE)
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

watch(
  () => props.option,
  () => render(),
  { deep: true },
)

// 运行中切换「减少动态效果」时，立即停掉正在进行的逐点绘制
watch(reduced, (isReduced) => {
  if (isReduced) {
    disposeSweep()
    chart?.setOption(props.option, MERGE)
  }
})

onBeforeUnmount(() => {
  disposeSweep()
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
}
</style>
