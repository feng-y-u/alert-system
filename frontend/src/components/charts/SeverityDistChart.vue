<template>
  <BaseChart :option="option" merge-update height="260px" />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import {
  categoryAxis,
  chartAnimation,
  CHART_COLORS,
  grid,
  tooltip,
  valueAxis,
} from '../../utils/chart'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const NAME_MAP = { low: '低', medium: '中', high: '高' }
const COLOR_MAP = {
  low: CHART_COLORS.info,
  medium: CHART_COLORS.warning,
  high: CHART_COLORS.danger,
}

const option = computed(() => ({
  ...chartAnimation,
  tooltip: tooltip('axis', { formatter: '{b}级别: {c} 条' }),
  grid: grid(),
  xAxis: categoryAxis(
    props.data.map((s) => NAME_MAP[s.name] ?? s.name),
    { boundaryGap: true },
  ),
  yAxis: valueAxis({ minInterval: 1 }),
  series: [
    {
      name: '严重级别',
      type: 'bar',
      barWidth: '38%',
      data: props.data.map((s) => ({
        value: s.value,
        itemStyle: {
          color: COLOR_MAP[s.name] ?? CHART_COLORS.brand,
          borderRadius: [7, 7, 0, 0],
        },
      })),
    },
  ],
}))
</script>
