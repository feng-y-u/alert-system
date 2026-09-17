/**
 * 数值来源解析：把 number / string / ref / computed / getter 统一解析为有限数字。
 *
 * 存在的意义：`useCountUp` 的入参可能是 props 数值、computed ref 或 getter，
 * 而 `Number(computedRef)` 的结果是 **NaN**（ref 对象没有数值语义），
 * 一旦直接 Number() 化就会静默退化成 0 —— 仪表盘"待处理告警"显示 0
 * 却与告警列表不符，正是这个原因造成的。
 *
 * 本文件不 import 任何模块，便于用纯 Node 直接做单元验证。
 */

/**
 * @param {unknown} source 数值来源：number | string | ref | computed | getter | null/undefined
 * @param {number} fallback 无法解析为有限数字时的回退值
 * @returns {number}
 */
export function resolveNumericSource(source, fallback = 0) {
  // Vue 的 ref / computed 统一有 .value；getter 是函数
  let raw = source
  if (raw !== null && typeof raw === 'object' && 'value' in raw) {
    raw = raw.value
  }
  if (typeof raw === 'function') {
    raw = raw()
  }
  if (raw !== null && typeof raw === 'object' && 'value' in raw) {
    // getter 返回的仍是 ref 的情况（例如 () => props.value 里 props.value 本身是 ref）
    raw = raw.value
  }

  const num = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(num) ? num : fallback
}
