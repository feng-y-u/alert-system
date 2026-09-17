<template>
  <BaseChart :option="option" :height="height" />
</template>

<script setup>
import { computed } from 'vue'

import BaseChart from './BaseChart.vue'
import { useReducedMotion } from '../../composables/useReducedMotion'
import {
  barSeries,
  categoryAxis,
  chartMotion,
  CHART_COLORS,
  grid,
  tooltip,
  valueAxis,
} from '../../utils/chart'

const props = defineProps({
  data: { type: Array, default: () => [] },
  height: { type: String, default: 'clamp(200px, 26vw, 260px)' },
})

const reduced = useReducedMotion()

const NAME_MAP = { low: '低', medium: '中', high: '高' }
const COLOR_MAP = {
  low: CHART_COLORS.info,
  medium: CHART_COLORS.warning,
  high: CHART_COLORS.danger,
}

const option = computed(() => ({
  ...chartMotion('bar', reduced.value),
  tooltip: tooltip('axis', { formatter: '{b}级别: {c} 条' }),
  grid: grid(),
  xAxis: categoryAxis(
    props.data.map((s) => NAME_MAP[s.name] ?? s.name),
    { boundaryGap: true },
  ),
  yAxis: valueAxis({ minInterval: 1 }),
  series: [
    barSeries({
      id: 'severity-dist',
      name: '严重级别',
      items: props.data.map((s) => ({
        value: s.value,
        color: COLOR_MAP[s.name] ?? CHART_COLORS.brand,
      })),
    }),
  ],
}))
</script>
