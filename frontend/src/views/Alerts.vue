<template>
  <div class="alerts-page">
    <h1 class="page-title">告警列表</h1>
    <div class="placeholder-card">
      <el-icon :size="48" color="#9ca3af"><Warning /></el-icon>
      <p class="placeholder-text">告警功能开发中，敬请期待</p>
      <p class="placeholder-sub">第5周实现</p>
    </div>
  </div>
</template>

<script setup>
import { Warning } from '@element-plus/icons-vue'
</script>

<style scoped>
.alerts-page {
  padding: 32px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
}

.placeholder-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 64px;
  text-align: center;
}

.placeholder-text {
  font-size: 16px;
  color: #6b7280;
  margin-top: 16px;
}

.placeholder-sub {
  font-size: 14px;
  color: #9ca3af;
  margin-top: 8px;
}
</style>