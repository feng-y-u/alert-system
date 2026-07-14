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

const typeNameMap = { frequency: '频率异常', device: '设备异常' }

const buildOption = (data) => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, textStyle: { color: '#6b7280', fontSize: 12 } },
  series: [{
    type: 'pie',
    radius: ['45%', '70%'],
    center: ['50%', '45%'],
    avoidLabelOverlap: false,
    label: { show: false },
    labelLine: { show: false },
    data: data.map((item, i) => ({
      name: typeNameMap[item.name] || item.name,
      value: item.value,
      itemStyle: { color: ['#111827', '#F59E0B'][i % 2] },
    })),
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
