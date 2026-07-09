<template>
  <div class="pagination-wrapper">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      @change="handleChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  skip: { type: Number, default: 0 },
  limit: { type: Number, default: 50 }
})

const emit = defineEmits(['change'])

const currentPage = computed({
  get: () => Math.floor(props.skip / props.limit) + 1,
  set: (val) => {
    const skip = (val - 1) * pageSize.value
    emit('change', skip, pageSize.value)
  }
})

const pageSize = computed({
  get: () => props.limit,
  set: (val) => {
    emit('change', 0, val)
  }
})

const handleChange = () => {
  const skip = (currentPage.value - 1) * pageSize.value
  emit('change', skip, pageSize.value)
}
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 20px;
}
</style>