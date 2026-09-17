import { onBeforeUnmount, ref } from 'vue'

import { prefersReducedMotion } from '../utils/motion'

/**
 * 响应式的「减少动态效果」偏好。
 *
 * 与 `prefersReducedMotion()` 的区别：这里会监听系统设置的**实时变化**，
 * 图表动画（ECharts 的 animation 开关）必须依赖它才能即时降级——
 * 原先在模块顶层读一次 matchMedia 的写法在运行时切换是无效的。
 *
 * @returns {import('vue').Ref<boolean>}
 */
export function useReducedMotion() {
  const reduced = ref(prefersReducedMotion())

  if (typeof window === 'undefined' || !window.matchMedia) {
    return reduced
  }

  const query = window.matchMedia('(prefers-reduced-motion: reduce)')
  const onChange = (event) => {
    reduced.value = event.matches
  }

  query.addEventListener('change', onChange)
  onBeforeUnmount(() => query.removeEventListener('change', onChange))

  return reduced
}
