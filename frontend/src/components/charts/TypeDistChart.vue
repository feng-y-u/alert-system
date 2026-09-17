<template>
  <BaseChart :option="option" :height="height" />
</template>

<script setup>
import { computed } from 'vue'

import BaseChart from './BaseChart.vue'
import { useReducedMotion } from '../../composables/useReducedMotion'
import { chartMotion, CHART_COLORS, donutSeries, tooltip } from '../../utils/chart'

const props = defineProps({
  data: { type: Array, default: () => [] },
  height: { type: String, default: 'clamp(200px, 26vw, 260px)' },
})

const reduced = useReducedMotion()

const NAME_MAP = { frequency: '频率异常', device: '设备异常' }
const COLORS = [
  CHART_COLORS.brand,
  CHART_COLORS.warning,
  CHART_COLORS.success,
  CHART_COLORS.info,
]

const option = computed(() => ({
  ...chartMotion('pie', reduced.value),
  tooltip: tooltip('item', { formatter: '{b}: {c} ({d}%)' }),
  legend: {
    bottom: 0,
    itemWidth: 8,
    itemHeight: 8,
    icon: 'circle',
    textStyle: { color: '#64748b', fontSize: 12 },
  },
  series: [
    donutSeries({
      id: 'type-dist',
      name: '告警类型',
      items: props.data.map((item, index) => ({
        name: NAME_MAP[item.name] ?? item.name,
        value: item.value,
        color: COLORS[index % COLORS.length],
      })),
    }),
  ],
}))
</script>
