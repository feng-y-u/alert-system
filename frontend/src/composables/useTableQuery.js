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
export function useTableQuery(fetcher, { limit: defaultLimit = 20 } = {}) {
  const items = ref([])
  const total = ref(0)
  const skip = ref(0)
  const limit = ref(defaultLimit)
  const filters = ref({})

  async function load() {
    const res = await fetcher({
      skip: skip.value,
      limit: limit.value,
      ...filters.value,
    })
    items.value = res?.items ?? []
    total.value = res?.total ?? 0
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
