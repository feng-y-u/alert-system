export function formatDateTime(isoString) {
  if (!isoString) return '-'
  const normalized = ensureTimezone(isoString)
  const date = new Date(normalized)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).replace(/\//g, '-')
}

function ensureTimezone(isoString) {
  if (isoString.endsWith('Z')) return isoString
  if (/[+-]\d{2}:\d{2}$/.test(isoString)) return isoString
  return isoString + 'Z'
}
