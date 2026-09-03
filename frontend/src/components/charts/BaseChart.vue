<template>
  <div ref="container" class="base-chart" :style="{ height }" />
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  /** 完整的 ECharts option，由各图表组件负责构造 */
  option: { type: Object, required: true },
  height: { type: String, default: '320px' },
  /**
   * 数据更新时的模式：
   * - false（默认）：整图重绘，重放入场动画。适用于 X 轴类目会整体变化的图
   *   （如趋势图 7 天 ↔ 30 天），逐点形变的中间态毫无意义，重画更干净。
   * - true：合并模式，新旧 series 按索引合并平滑过渡。适用于类目稳定的图
   *   （如分布图），扇区扫动 / 柱子升降的过渡自然。
   */
  mergeUpdate: { type: Boolean, default: false },
})

const container = ref(null)
let chart = null
let observer = null

function render() {
  if (!container.value) return
  if (!chart) chart = echarts.init(container.value)
  chart.setOption(props.option, { notMerge: !props.mergeUpdate })
}

onMounted(() => {
  render()
  // 侧边栏折叠/窗口变化都要重排，否则画布尺寸会停留在初始值
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(container.value)
})

watch(
  () => props.option,
  () => render(),
  { deep: true },
)

onBeforeUnmount(() => {
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
