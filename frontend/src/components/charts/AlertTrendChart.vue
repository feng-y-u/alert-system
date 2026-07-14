<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

const buildOption = (data) => ({
  animationDuration: 2500,
  animationEasing: 'cubicOut',
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#e5e7eb',
    borderWidth: 1,
    textStyle: { color: '#111827' },
    padding: [12, 16],
  },
  grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
  xAxis: {
    type: 'category',
    data: data.map(t => t.date),
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisTick: { show: false },
    axisLabel: { color: '#6b7280', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
    axisLabel: { color: '#6b7280', fontSize: 12 },
  },
  series: [{
    type: 'line',
    data: data.map(t => t.count),
    smooth: true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: {
      width: 3,
      color: '#F59E0B',
      shadowColor: 'rgba(245, 158, 11, 0.3)',
      shadowBlur: 10,
      shadowOffsetY: 5,
    },
    itemStyle: { color: '#F59E0B', borderWidth: 2, borderColor: '#fff' },
    areaStyle: {
      opacity: 0.8,
      color: {
        type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
        colorStops: [
          { offset: 0, color: 'rgba(245, 158, 11, 0.2)' },
          { offset: 1, color: 'rgba(245, 158, 11, 0)' },
        ],
      },
    },
  }],
})

const render = () => {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption(props.data))
}

onMounted(render)
watch(() => props.data, render)
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart-container {
  height: 320px;
}
</style>
