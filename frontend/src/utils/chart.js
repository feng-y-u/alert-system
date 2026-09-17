/**
 * ECharts 共有配置与**按图形语义区分**的动效预设。
 *
 * 与旧实现（`chartAnimation` 一份 900ms 配置给四种图共用）的差别：
 * 折线要「画」出来、柱要「长」出来、环要「扫」出来，
 * 三者对时长与错峰的诉求完全不同，因此这里按 kind 分派；
 * 数据更新的过渡时长统一比入场短，避免拖沓。
 *
 * 缓动与时长取自 utils/motion.js，与 CSS 侧同一套节奏。
 */

import { DURATION } from './motion'

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
 * 图表动画配置。
 *
 * @param {'line'|'bar'|'pie'} kind 图形类型，决定入场时长与错峰步长
 * @param {boolean} reduced 系统是否要求减少动态效果
 * @returns {object} 可直接展开进 ECharts option 的动画字段
 */
export function chartMotion(kind = 'line', reduced = false) {
  if (reduced) {
    // 完全关闭动画：数据仍然正确呈现，只是没有过渡
    return { animation: false, animationDuration: 0, animationDurationUpdate: 0 }
  }

  const base = {
    animation: true,
    // 数据点超过阈值时 ECharts 自动跳过动画，避免大数据量下掉帧
    animationThreshold: 800,
    animationEasing: 'cubicOut',
    // 数据更新只做形变，不做入场
    animationEasingUpdate: 'cubicInOut',
    animationDurationUpdate: DURATION.chartUpdate,
  }

  switch (kind) {
    case 'bar':
      // 柱子自左向右依次长出
      return {
        ...base,
        animationDuration: DURATION.chartBar,
        animationDelay: (index) => index * 45,
      }
    case 'pie':
      // 扇区由内向外依次扫出（expansion 比整体 scale 更克制）
      return {
        ...base,
        animationDuration: DURATION.chartPie,
        animationType: 'expansion',
        animationDelay: (index) => index * 70,
      }
    case 'line':
    default:
      // 折线的路径由 ECharts 自身插值绘制；这里的延迟让数据点按 X 顺序出现。
      // 额外的「从左到右逐点绘制」由 BaseChart 的 entrance="sweep" 负责。
      return {
        ...base,
        animationDuration: DURATION.chartLine,
        animationDelay: (index) => index * 6,
      }
  }
}

/**
 * 折线 + 面积系列（两张趋势图此前各自复制了这段结构，只差颜色与名称）。
 */
export function lineSeries({ id, name, data, color, showSymbol = false }) {
  return {
    id,
    name,
    type: 'line',
    data,
    smooth: true,
    // 沿 X 轴单调的平滑：0 平原 → 真实数据的跳变处不会过冲下坠到零轴以下
    smoothMonotone: 'x',
    symbol: 'circle',
    symbolSize: 6,
    showSymbol,
    lineStyle: {
      width: 2.5,
      color,
      shadowColor: withAlpha(color, 0.28),
      shadowBlur: 12,
      shadowOffsetY: 6,
    },
    itemStyle: { color, borderWidth: 2, borderColor: '#fff' },
    areaStyle: areaFill(color),
    emphasis: { focus: 'series' },
  }
}

/**
 * 柱状系列（严重级别分布）。
 *
 * @param {{ items: Array<{ value: number, color: string }>, barWidth?: string }} params
 */
export function barSeries({ id, name, items, barWidth = '38%' }) {
  return {
    id,
    name,
    type: 'bar',
    barWidth,
    data: items.map((item) => ({
      value: item.value,
      itemStyle: { color: item.color, borderRadius: [7, 7, 0, 0] },
    })),
    emphasis: { focus: 'series' },
  }
}

/**
 * 环形（甜甜圈）系列（告警类型分布）。
 *
 * @param {{ items: Array<{ name: string, value: number, color: string }> }} params
 */
export function donutSeries({ id, name, items, center = ['50%', '44%'] }) {
  return {
    id,
    name,
    type: 'pie',
    radius: ['52%', '76%'],
    center,
    avoidLabelOverlap: false,
    label: { show: false },
    labelLine: { show: false },
    itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 5 },
    data: items.map((item) => ({
      name: item.name,
      value: item.value,
      itemStyle: { color: item.color },
    })),
    emphasis: { scale: false, itemStyle: { shadowBlur: 12, shadowColor: 'rgba(15,23,42,0.14)' } },
  }
}
