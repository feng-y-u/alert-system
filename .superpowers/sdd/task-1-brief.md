### Task 1: StatusTag — badge 样式

**Files:**
- Modify: `frontend/src/components/common/StatusTag.vue`

**Interfaces:**
- Consumes: `props.status: 'success' | 'failure'`（不变）
- Produces: 带背景色圆角 badge 的 `<span>`

- [ ] **Step 1: 重写 StatusTag 样式**

将纯色文字改为浅色背景 badge，色值直接从 UI 规范取：

```vue
<template>
  <span class="status-tag" :class="statusClass">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true }
})

const statusClass = computed(() => ({
  'status-tag--success': props.status === 'success',
  'status-tag--failure': props.status === 'failure'
}))

const label = computed(() => ({
  success: '成功',
  failure: '失败'
}[props.status] || props.status))
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
}

.status-tag--success {
  background: #D1FAE5;
  color: #10B981;
}

.status-tag--failure {
  background: #FEE2E2;
  color: #EF4444;
}
</style>
```

- [ ] **Step 2: 确认无其他组件引用此组件导致样式断裂**

```bash
grep -r "StatusTag" frontend/src/ --include="*.vue" --include="*.js"
```

预期输出至少包含 `LogTable.vue` 和 `StatusTag.vue` 自身。

- [ ] **Step 3: Commit**

```bash
cd e:/实习
git add frontend/src/components/common/StatusTag.vue
git commit -m "refactor: StatusTag badge style per UI spec"
```

---

