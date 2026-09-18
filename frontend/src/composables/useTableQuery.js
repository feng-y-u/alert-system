import { ref } from 'vue'
import { useAsyncData } from './useAsyncData'

/**
 * 列表页通用取数逻辑。
 *
 * 后端分页用 skip/limit 而非 page/pageSize，且「筛选 → 重置 skip」「翻页 → 保留筛选」
 * 这套规则在登录日志页与告警页完全一样，收在这里。
 *
 * @param {Function} fetcher 形如 ({ skip, limit, ...filters }) => Promise<{ items, total }>
 * @param {{ limit?: number }} options
 */
/** 计算承载 ``total`` 条数据时最后一个非空页的 skip */
function lastValidSkipFor(total, limit) {
  if (total <= 0) return 0
  const perPage = limit > 0 ? limit : 1
  return Math.floor((total - 1) / perPage) * perPage
}

export function useTableQuery(fetcher, { limit: defaultLimit = 20 } = {}) {
  const items = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(defaultLimit)
  const filters = ref({})

  function fetchPage(atSkip, atLimit) {
    return fetcher({
      skip: atSkip,
      limit: atLimit,
      ...filters.value,
    })
  }

  async function load() {
    const res = await fetchPage(skip.value, limit.value)
    const newTotal = res?.total ?? 0

    // 当前页已越界（写操作把数据改少、或末页被清空）：回退到最后一个有效页重新取数。
    // 只置 skip 不重新请求的话，界面会停在一张空白表格上（BUG-009）。
    const lastValid = lastValidSkipFor(newTotal, limit.value)
    if (newTotal > 0 && skip.value > lastValid) {
      skip.value = lastValid
      const retry = await fetchPage(lastValid, limit.value)
      items.value = retry?.items ?? []
      total.value = retry?.total ?? 0
      return
    }

    if (newTotal === 0) skip.value = 0

    items.value = res?.items ?? []
    total.value = newTotal
  }

  const { loading, error, retryCooldown, execute } = useAsyncData(load)

  /** 条件查询：回到第一页 */
  function search(params) {
    skip.value = 0
    filters.value = params
    execute()
  }

  /** 重置条件：清空筛选并回到第一页 */
  function reset() {
    skip.value = 0
    filters.value = {}
    execute()
  }

  function changePage(newSkip, newLimit) {
    skip.value = newSkip
    limit.value = newLimit
    execute()
  }

  /** 写操作（改状态、批量删除）后原地刷新，保留当前页与筛选 */
  function refresh() {
    execute()
  }

  return {
    items,
    total,
    skip,
    limit,
    filters,
    loading,
    error,
    retryCooldown,
    execute,
    search,
    reset,
    changePage,
    refresh,
  }
}
