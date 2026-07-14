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

const severityNameMap = { low: '低', medium: '中', high: '高' }
const severityColorMap = { low: '#3B82F6', medium: '#F59E0B', high: '#EF4444' }

const buildOption = (data) => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
  xAxis: {
    type: 'category',
    data: data.map(s => severityNameMap[s.name] || s.name),
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisTick: { show: false },
    axisLabel: { color: '#6b7280', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
    axisLabel: { color: '#6b7280', fontSize: 12 },
    minInterval: 1,
  },
  series: [{
    type: 'bar',
    data: data.map(s => ({
      value: s.value,
      itemStyle: { color: severityColorMap[s.name] || '#111827' },
    })),
    barWidth: '40%',
    itemStyle: { borderRadius: [6, 6, 0, 0] },
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
  height: 280px;
}
</style>
