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
  /** 窄屏下由父级传入更矮的高度，避免趋势图占据整屏 */
  height: { type: String, default: 'clamp(220px, 30vw, 300px)' },
})

const reduced = useReducedMotion()

const option = computed(() => ({
  ...chartMotion('line', reduced.value),
  tooltip: tooltip('axis'),
  grid: grid(),
  xAxis: categoryAxis(props.data.map((d) => d.date)),
  yAxis: valueAxis(),
  series: [
    lineSeries({
      id: 'login-trend',
      name: '登录次数',
      data: props.data.map((d) => d.count),
      color: CHART_COLORS.brand,
      showSymbol: props.data.length <= 15,
    }),
  ],
}))
</script>
