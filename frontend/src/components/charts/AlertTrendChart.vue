<template>
  <BaseChart :option="option" entrance="sweep" :height="height" />
</template>

<script setup>
import { computed } from 'vue'

import BaseChart from './BaseChart.vue'
import { useReducedMotion } from '../../composables/useReducedMotion'
import {
  categoryAxis,
  chartMotion,
  CHART_COLORS,
  grid,
  lineSeries,
  tooltip,
  valueAxis,
} from '../../utils/chart'

const props = defineProps({
  data: { type: Array, default: () => [] },
  height: { type: String, default: 'clamp(220px, 30vw, 300px)' },
})

const reduced = useReducedMotion()

const option = computed(() => ({
  ...chartMotion('line', reduced.value),
  tooltip: tooltip('axis'),
  grid: grid(),
  xAxis: categoryAxis(props.data.map((d) => d.date)),
  // 告警数是整数，避免出现 0.5 这样的刻度
  yAxis: valueAxis({ minInterval: 1 }),
  series: [
    lineSeries({
      id: 'alert-trend',
      name: '告警数',
      data: props.data.map((d) => d.count),
      color: CHART_COLORS.warning,
      showSymbol: props.data.length <= 15,
    }),
  ],
}))
</script>
