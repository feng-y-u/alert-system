/** 后端返回的时间可能是无时区的 naive 串，统一按 UTC 解析后再本地化 */
function ensureTimezone(isoString) {
  if (isoString.endsWith('Z')) return isoString
  if (/[+-]\d{2}:\d{2}$/.test(isoString)) return isoString
  return isoString + 'Z'
}

function toDate(isoString) {
  if (!isoString) return null
  const date = new Date(ensureTimezone(isoString))
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatDateTime(isoString) {
  const date = toDate(isoString)
  if (!date) return '-'
  return date
    .toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
    .replace(/\//g, '-')
}

export function formatTime(isoString) {
  const date = toDate(isoString)
  if (!date) return '-'
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

export function formatNumber(num) {
  if (num === null || num === undefined || Number.isNaN(num)) return '0'
  return Number(num).toLocaleString('zh-CN')
}

/** 相对时间：刚刚 / N 分钟前 / N 天前，超过 30 天回退为完整日期时间 */
export function formatRelative(isoString) {
  const date = toDate(isoString)
  if (!date) return '-'

  const diff = Date.now() - date.getTime()
  const minute = 60 * 1000
  const hour = 60 * minute
  const day = 24 * hour

  if (diff < 0) return formatDateTime(isoString)
  if (diff < 3 * minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`
  if (diff < 30 * day) return `${Math.floor(diff / day)} 天前`
  return formatDateTime(isoString)
}

/**
 * 简易防抖。
 * 原先 Dashboard 从 lodash-es 引入 debounce，但 lodash-es 只是 element-plus 的
 * 传递依赖、并未声明在 package.json 中，这里自带实现以消除隐式依赖。
 */
export function debounce(fn, wait = 300) {
  let timer = null
  return function debounced(...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), wait)
  }
}
