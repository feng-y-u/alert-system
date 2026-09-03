<template>
  <BaseChart :option="option" height="300px" />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import {
  areaFill,
  categoryAxis,
  CHART_COLORS,
  grid,
  chartAnimation,
  tooltip,
  valueAxis,
  withAlpha,
} from '../../utils/chart'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const WARN = CHART_COLORS.warning

const option = computed(() => ({
  ...chartAnimation,
  // 切换时间范围时整图重绘（notMerge），重放画线动画，750ms 比 900ms 更利落
  animationDuration: 750,
  tooltip: tooltip('axis'),
  grid: grid(),
  xAxis: categoryAxis(props.data.map((d) => d.date)),
  yAxis: valueAxis({ minInterval: 1 }),
  series: [
    {
      name: '告警数',
      type: 'line',
      data: props.data.map((d) => d.count),
      smooth: true,
      // 沿 X 轴单调的平滑：0 平原 → 真实数据的跳变处不会过冲下坠到零轴以下
      smoothMonotone: 'x',
      symbol: 'circle',
      symbolSize: 7,
      showSymbol: props.data.length <= 15,
      lineStyle: {
        width: 2.5,
        color: WARN,
        shadowColor: withAlpha(WARN, 0.3),
        shadowBlur: 12,
        shadowOffsetY: 6,
      },
      itemStyle: { color: WARN, borderWidth: 2, borderColor: '#fff' },
      areaStyle: areaFill(WARN),
      emphasis: { focus: 'series' },
    },
  ],
}))
</script>
