<template>
  <div class="dashboard" :class="{ 'is-refreshing': isRefreshing }">
    <ErrorState
      v-if="error"
      title="仪表盘数据加载失败"
      description="无法获取统计数据，请稍后重试"
      :cooldown="retryCooldown"
      @retry="execute"
    />

    <template v-else>
      <!-- 统计卡片 -->
      <div class="stat-grid">
        <StatCard
          label="今日登录"
          :value="stats.todayLogins"
          :icon="TrendCharts"
          tone="brand"
          hint="按 UTC 自然日统计"
        />
        <StatCard
          label="待处理告警"
          :value="stats.pendingAlerts"
          :icon="Warning"
          :tone="stats.pendingAlerts > 0 ? 'warning' : 'success'"
          :hint="stats.pendingAlerts > 0 ? '需要管理员跟进' : '暂无待处理事项'"
        />
        <StatCard
          label="活跃用户"
          :value="stats.activeUsers"
          :icon="User"
          tone="info"
          hint="今日有登录记录的账号"
        />
      </div>

      <!-- 登录趋势 -->
      <SectionCard
        title="登录趋势"
        :subtitle="`近 ${days} 天的登录次数变化`"
      >
        <template #actions>
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button value="week">近 7 天</el-radio-button>
            <el-radio-button value="month">近 30 天</el-radio-button>
          </el-radio-group>
        </template>

        <LoginTrendChart v-if="trend.length" :data="trend" />
        <EmptyState
          v-else
          title="暂无登录数据"
          description="校园系统上报登录日志后，这里会显示趋势曲线"
          :icon="DataLine"
        />
      </SectionCard>

      <!-- 告警趋势 -->
      <SectionCard title="告警趋势" :subtitle="`近 ${days} 天的告警数量变化`">
        <AlertTrendChart v-if="alertTrend.length" :data="alertTrend" />
        <EmptyState
          v-else
          title="暂无告警"
          description="未检测到异常登录行为，这是好事"
          :icon="CircleCheck"
        />
      </SectionCard>

      <!-- 分布图 -->
      <div class="dist-grid">
        <SectionCard title="告警类型分布">
          <TypeDistChart v-if="typeDist.length" :data="typeDist" />
          <EmptyState v-else title="暂无数据" />
        </SectionCard>

        <SectionCard title="严重级别分布">
          <SeverityDistChart v-if="severityDist.length" :data="severityDist" />
          <EmptyState v-else title="暂无数据" />
        </SectionCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import api from '../api'
import { getAlertStats } from '../api/stats'
import { useAsyncData } from '../composables/useAsyncData'
import { debounce } from '../utils/format'
import SectionCard from '../components/common/SectionCard.vue'
import StatCard from '../components/common/StatCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorState from '../components/common/ErrorState.vue'
import LoginTrendChart from '../components/charts/LoginTrendChart.vue'
import AlertTrendChart from '../components/charts/AlertTrendChart.vue'
import TypeDistChart from '../components/charts/TypeDistChart.vue'
import SeverityDistChart from '../components/charts/SeverityDistChart.vue'
import {
  CircleCheck,
  DataLine,
  TrendCharts,
  User,
  Warning,
} from '@element-plus/icons-vue'

const stats = ref({ todayLogins: 0, pendingAlerts: 0, activeUsers: 0 })
const trend = ref([])
const alertTrend = ref([])
const typeDist = ref([])
const severityDist = ref([])
const timeRange = ref('week')
const initialized = ref(false)

const days = computed(() => (timeRange.value === 'month' ? 30 : 7))

async function loadDashboard() {
  const [loginRes, alertRes] = await Promise.all([
    api.get('/api/stats', { params: { days: days.value } }),
    getAlertStats(days.value),
  ])

  stats.value = {
    todayLogins: loginRes.todayLogins,
    pendingAlerts: loginRes.pendingAlerts,
    activeUsers: loginRes.activeUsers,
  }
  trend.value = loginRes.loginTrend ?? []
  alertTrend.value = alertRes.alertTrend ?? []
  typeDist.value = alertRes.typeDist ?? []
  severityDist.value = alertRes.severityDist ?? []
  initialized.value = true
}

const { loading, error, retryCooldown, execute } = useAsyncData(loadDashboard, {
  immediate: true,
})

// 切换时间范围防抖，避免快速连点打出多次请求
watch(days, debounce(() => execute(), 250))

// 仅在"已有数据后的刷新"（切换时间范围）时变暗提示，
// 首次加载时入场动画本身就在播放，不需要额外反馈
const isRefreshing = computed(() => loading.value && initialized.value)
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

/* ===== 入场动画：卡片 → 趋势图 → 分布图 依次浮现 ===== */
@keyframes rise-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dashboard > * {
  animation: rise-in 0.5s var(--ease) backwards;
  transition: opacity 0.18s ease;
}

.dashboard > *:nth-child(1) {
  animation-delay: 0.05s;
}
.dashboard > *:nth-child(2) {
  animation-delay: 0.14s;
}
.dashboard > *:nth-child(3) {
  animation-delay: 0.22s;
}
.dashboard > *:nth-child(4) {
  animation-delay: 0.3s;
}

/* 统计卡与分布卡内部再各自错开一拍 */
.stat-grid > *,
.dist-grid > * {
  animation: rise-in 0.5s var(--ease) backwards;
}

.stat-grid > *:nth-child(1) {
  animation-delay: 0.05s;
}
.stat-grid > *:nth-child(2) {
  animation-delay: 0.13s;
}
.stat-grid > *:nth-child(3) {
  animation-delay: 0.21s;
}

.dist-grid > *:nth-child(1) {
  animation-delay: 0.34s;
}
.dist-grid > *:nth-child(2) {
  animation-delay: 0.42s;
}

/* ===== 切换时间范围时：拉取数据期间内容轻微变暗 ===== */
.dashboard.is-refreshing > * {
  opacity: 0.62;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
}

.dist-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 22px;
}

/* 系统开启"减少动态效果"时不播放入场动画 */
@media (prefers-reduced-motion: reduce) {
  .dashboard > *,
  .stat-grid > *,
  .dist-grid > * {
    animation: none;
  }
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .dist-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
}
</style>
