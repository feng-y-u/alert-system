/**
 * 动效令牌与缓动函数（唯一事实来源）。
 *
 * 设计原则：动画服务于「数据正在被加载和呈现」的感知，而不是装饰。
 * 因此只有三个层级，避免每个元素各写一套数值：
 *
 * - fast   微交互（hover / 焦点 / 按下）
 * - base   状态切换（展开 / Tab / 筛选 / 数值变化）
 * - slow   内容与图层入场（卡片、区块）
 *
 * CSS 侧在 App.vue 以同名变量（--motion-fast 等）暴露，两边数值同源；
 * 修改动效节奏时改这里 + App.vue 的变量即可，不要在组件里写魔法数字。
 */

/** 时长（毫秒），与 App.vue 的 --motion-* 一一对应 */
export const DURATION = {
  fast: 140,
  base: 220,
  slow: 380,
  /** 图表入场：折线要「画」出来，需要比 UI 元素更长 */
  chartLine: 720,
  chartBar: 520,
  chartPie: 620,
  /** 图表数据更新：只做形变，必须比入场短，避免拖沓 */
  chartUpdate: 420,
}

/** CSS 缓动曲线字面量 */
export const EASING = {
  /** 通用状态切换：两端对称，适合可逆操作 */
  standard: 'cubic-bezier(0.2, 0, 0.2, 1)',
  /** 入场：快速起步、尾部收敛，无回弹 */
  enter: 'cubic-bezier(0.16, 1, 0.3, 1)',
  /** 位移动画（侧栏、面板） */
  move: 'cubic-bezier(0.4, 0, 0.2, 1)',
}

/** 缓动函数（rAF 数值动画用） */
export const easeOutCubic = (t) => 1 - Math.pow(1 - t, 3)
export const easeOutQuint = (t) => 1 - Math.pow(1 - t, 5)

/** 入场错峰的默认节奏：步长 55ms、上限 330ms（≈6 个元素后不再累加） */
export const REVEAL_TIMING = {
  step: 55,
  max: 330,
}

/**
 * 实时读取系统「减少动态效果」偏好。
 *
 * 刻意不做模块级缓存：用户可以在应用运行期间切换系统设置，
 * 缓存会导致切换后仍然播放动画（旧实现在 StatCard 里踩过这个坑）。
 */
export function prefersReducedMotion() {
  if (typeof window === 'undefined' || !window.matchMedia) return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * 计算入场延迟，替代原先散落在 CSS 里的 nth-child 硬编码。
 *
 * 好处：元素顺序变化、断点改变列数、动态增删卡片时，延迟自动跟随，
 * 不需要再去数 nth-child。
 *
 * @param {number} index 元素在视觉序列中的位置（从 0 开始）
 * @param {{ base?: number, step?: number, max?: number }} options
 * @returns {Record<string, string>} 可直接绑到 :style 的 CSS 变量
 */
export function revealStyle(index = 0, options = {}) {
  const { base = 0, step = REVEAL_TIMING.step, max = REVEAL_TIMING.max } = options
  const delay = base + Math.min(Math.max(index, 0) * step, max)
  return { '--reveal-delay': `${delay}ms` }
}
