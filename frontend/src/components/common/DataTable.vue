<template>
  <div class="data-table">
    <ErrorState
      v-if="error"
      :cooldown="cooldown"
      :title="errorTitle"
      @retry="emit('retry')"
    />

    <template v-else>
      <el-table
        v-loading="loading"
        :data="items"
        stripe
        class="data-table__el"
        :row-key="rowKey"
      >
        <slot />

        <template #empty>
          <EmptyState :title="emptyTitle" :description="emptyDescription" />
        </template>
      </el-table>

      <TablePagination
        :total="total"
        :skip="skip"
        :limit="limit"
        @change="(s, l) => emit('page-change', s, l)"
      />
    </template>
  </div>
</template>

<script setup>
import EmptyState from './EmptyState.vue'
import ErrorState from './ErrorState.vue'
import TablePagination from './TablePagination.vue'

defineProps({
  items: { type: Array, required: true },
  total: { type: Number, default: 0 },
  skip: { type: Number, default: 0 },
  limit: { type: Number, default: 20 },
  loading: { type: Boolean, default: false },
  error: { type: Boolean, default: false },
  cooldown: { type: Boolean, default: false },
  rowKey: { type: String, default: 'id' },
  emptyTitle: { type: String, default: '暂无数据' },
  emptyDescription: { type: String, default: '' },
  errorTitle: { type: String, default: '数据加载失败' },
})

const emit = defineEmits(['page-change', 'retry'])
</script>

<style scoped>
.data-table {
  width: 100%;
}
</style>

<style>
/* 非 scoped：需要穿透到 Element Plus 表格内部 */
.data-table__el .el-table__body td.el-table__cell .cell,
.data-table__el .el-table__header th.el-table__cell .cell {
  white-space: nowrap;
}

.data-table__el {
  border-radius: var(--r-md);
  overflow: hidden;
}
</style>
