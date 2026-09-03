<template>
  <BaseChart :option="option" merge-update height="260px" />
</template>

<script setup>
import { computed } from 'vue'
import BaseChart from './BaseChart.vue'
import { chartAnimation, CHART_COLORS, tooltip } from '../../utils/chart'

const props = defineProps({
  data: { type: Array, default: () => [] },
})

const NAME_MAP = { frequency: '频率异常', device: '设备异常' }
const COLORS = [
  CHART_COLORS.brand,
  CHART_COLORS.warning,
  CHART_COLORS.success,
  CHART_COLORS.info,
]

const option = computed(() => ({
  ...chartAnimation,
  tooltip: tooltip('item', { formatter: '{b}: {c} ({d}%)' }),
  legend: {
    bottom: 0,
    itemWidth: 8,
    itemHeight: 8,
    icon: 'circle',
    textStyle: { color: '#64748b', fontSize: 12 },
  },
  series: [
    {
      name: '告警类型',
      type: 'pie',
      radius: ['52%', '76%'],
      center: ['50%', '44%'],
      avoidLabelOverlap: false,
      label: { show: false },
      labelLine: { show: false },
      itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 5 },
      data: props.data.map((item, i) => ({
        name: NAME_MAP[item.name] ?? item.name,
        value: item.value,
        itemStyle: { color: COLORS[i % COLORS.length] },
      })),
    },
  ],
}))
</script>
