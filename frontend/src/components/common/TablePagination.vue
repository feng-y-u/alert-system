<template>
  <div v-if="total > 0" class="table-pagination">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      background
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  skip: { type: Number, default: 0 },
  limit: { type: Number, default: 20 },
})

const emit = defineEmits(['change'])

// 后端是 skip/limit，Element 是 page/pageSize，在此换算
const currentPage = computed({
  get: () => Math.floor(props.skip / props.limit) + 1,
  set: (val) => emit('change', (val - 1) * pageSize.value, pageSize.value),
})

const pageSize = computed({
  get: () => props.limit,
  // 每页条数变化后留在第一页，否则可能落在越界页
  set: (val) => emit('change', 0, val),
})
</script>

<style scoped>
.table-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 16px 20px;
  border-top: 1px solid var(--border-soft);
}
</style>
