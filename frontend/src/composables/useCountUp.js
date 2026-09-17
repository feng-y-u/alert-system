import { onBeforeUnmount, ref, watch } from 'vue'

import { easeOutQuint, prefersReducedMotion } from '../utils/motion'
import { resolveNumericSource } from '../utils/number'

const DEFAULT_MIN = 320
const DEFAULT_MAX = 1100

/**
 * 平滑数值过渡（Count-Up）。
 *
 * 从 StatCard 内部抽出来，因为「数字平滑变化」是仪表盘、趋势标题、
 * 徽标计数都会用到的能力，不该每处复制一份 rAF 循环。
 *
 * 行为约定：
 * - 从**当前显示值**继续滚动，而不是每次跳回 0；
 * - 时长随差值自适应（差 1 用不着滚 900ms，差 1000 也不能一闪而过）；
 * - 只在**取整后的值变化时**才写响应式变量，减少无谓的 DOM 更新；
 * - 系统开启「减少动态效果」时直接落到终值，不做任何过渡；
 * - 组件卸载 / 目标值再次变化时取消上一次动画，避免多条 rAF 并发。
 *
 * ⚠️ `source` 允许是 number / string / ref / computed / getter，
 * 统一由 `resolveNumericSource` 解析。**不要**直接对它做 `Number()` 转换：
 * `Number(computedRef)` 的结果是 NaN，会静默退化成 0
 * （曾导致仪表盘「待处理告警」恒显示 0，见 docs/tech/14-评估与改进.md）。
 *
 * @param {number | string | import('vue').Ref | import('vue').ComputedRef | (() => number)} source
 * @param {{ minDuration?: number, maxDuration?: number, format?: (v: number) => string, immediate?: boolean }} options
 * @returns {{ display: import('vue').Ref<string>, isAnimating: import('vue').Ref<boolean> }}
 */
export function useCountUp(source, options = {}) {
  const {
    minDuration = DEFAULT_MIN,
    maxDuration = DEFAULT_MAX,
    format = (value) => String(Math.round(value)),
    immediate = true,
  } = options

  const readTarget = () => resolveNumericSource(source)

  const display = ref(format(readTarget()))
  const isAnimating = ref(false)

  /** 当前显示值（浮点，用于续算），与 display 的取整值保持同步 */
  let current = readTarget()
  let rafId = null
  let lastRounded = Math.round(current)

  function cancel() {
    if (rafId !== null) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    isAnimating.value = false
  }

  function setInstant(target) {
    cancel()
    current = target
    lastRounded = Math.round(target)
    display.value = format(target)
  }

  function animateTo(target) {
    if (prefersReducedMotion()) {
      setInstant(target)
      return
    }

    const delta = target - current
    if (Math.abs(delta) < 0.5) {
      setInstant(target)
      return
    }

    cancel()

    // 差值越大滚得越久，但限制在 [minDuration, maxDuration] 内
    const duration = Math.min(
      maxDuration,
      Math.max(minDuration, 240 + Math.abs(delta) * 12),
    )
    const from = current
    const startedAt = performance.now()
    isAnimating.value = true

    const step = (now) => {
      const progress = Math.min((now - startedAt) / duration, 1)
      current = from + delta * easeOutQuint(progress)
      const rounded = Math.round(current)
      if (rounded !== lastRounded) {
        lastRounded = rounded
        display.value = format(current)
      }
      if (progress < 1) {
        rafId = requestAnimationFrame(step)
      } else {
        rafId = null
        isAnimating.value = false
        // 收尾对齐到精确值，避免浮点误差留下 ±1 的偏差
        display.value = format(target)
        current = target
      }
    }

    rafId = requestAnimationFrame(step)
  }

  watch(
    readTarget,
    (target) => {
      animateTo(target)
    },
    { immediate },
  )

  onBeforeUnmount(cancel)

  return { display, isAnimating }
}
