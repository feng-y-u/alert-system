/**
 * ECharts 共有配置。
 * 四个图表此前各自重复了坐标轴、tooltip、网格的样式定义，收在这里统一。
 * 配色与 App.vue 设计 Token 保持一致。
 */

const AXIS_LINE = '#e6eaf1'
const SPLIT_LINE = '#eff2f7'
const LABEL_COLOR = '#64748b'

/** 图表主色板（与 brand / status 对应） */
export const CHART_COLORS = {
  brand: '#2563eb',
  brandLight: '#93c5fd',
  success: '#10b981',
  warning: '#f59e0b',
  danger: '#ef4444',
  info: '#0ea5e9',
}

export function tooltip(trigger = 'axis', extra = {}) {
  return {
    trigger,
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
    borderColor: AXIS_LINE,
    borderWidth: 1,
    padding: [10, 14],
    textStyle: { color: '#0f172a', fontSize: 13 },
    extraCssText: 'box-shadow: 0 8px 24px rgba(15,23,42,0.10); border-radius: 12px;',
    ...extra,
  }
}

export function categoryAxis(data, extra = {}) {
  return {
    type: 'category',
    data,
    boundaryGap: extra.boundaryGap ?? false,
    axisLine: { lineStyle: { color: AXIS_LINE } },
    axisTick: { show: false },
    axisLabel: { color: LABEL_COLOR, fontSize: 12 },
    ...extra,
  }
}

export function valueAxis(extra = {}) {
  return {
    type: 'value',
    splitLine: { lineStyle: { color: SPLIT_LINE, type: 'dashed' } },
    axisLabel: { color: LABEL_COLOR, fontSize: 12 },
    ...extra,
  }
}

export function grid(extra = {}) {
  return { left: 4, right: 12, top: 16, bottom: 4, containLabel: true, ...extra }
}

/** 面积图渐变，offset 0 → 1 由实到透明 */
export function areaFill(hex, from = 0.2, to = 0) {
  return {
    color: {
      type: 'linear',
      x: 0,
      y: 0,
      x2: 0,
      y2: 1,
      colorStops: [
        { offset: 0, color: withAlpha(hex, from) },
        { offset: 1, color: withAlpha(hex, to) },
      ],
    },
  }
}

export function withAlpha(hex, alpha) {
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

/**
 * 图表统一动效。
 * animationDuration / animationEasing：首次绘制（入场）
 * animationDurationUpdate / animationEasingUpdate：数据切换（近 7 天 ↔ 近 30 天）时的平滑过渡
 */
export const chartAnimation = {
  animation: true,
  animationDuration: 900,
  animationEasing: 'cubicOut',
  animationDurationUpdate: 550,
  animationEasingUpdate: 'cubicInOut',
}
