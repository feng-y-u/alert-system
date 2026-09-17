<template>
  <div class="dashboard">
    <ErrorState
      v-if="error"
      title="仪表盘数据加载失败"
      description="无法获取统计数据，请稍后重试"
      :cooldown="retryCooldown"
      @retry="execute"
    />

    <template v-else>
      <!-- 统计卡片：外壳先入场，数字待数据到位后再滚入 -->
      <div class="stat-grid">
        <StatCard
          v-for="(card, index) in statCards"
          :key="card.label"
          class="reveal"
          :style="revealStyle(index)"
          :label="card.label"
          :value="card.value"
          :icon="card.icon"
          :tone="card.tone"
          :hint="card.hint"
          :ready="ready"
        />
      </div>

      <!-- 趋势：外壳在统计卡之后入场，曲线在数据到位后从左到右绘制 -->
      <SectionCard
        class="reveal"
        :style="revealStyle(0, { base: 150 })"
        title="登录趋势"
        :subtitle="`近 ${days} 天的登录次数变化`"
        :loading="isRefreshing"
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

      <SectionCard
        class="reveal"
        :style="revealStyle(1, { base: 150 })"
        title="告警趋势"
        :subtitle="`近 ${days} 天的告警数量变化`"
        :loading="isRefreshing"
      >
        <AlertTrendChart v-if="alertTrend.length" :data="alertTrend" />
        <EmptyState
          v-else
          title="暂无告警"
          description="未检测到异常登录行为，这是好事"
          :icon="CircleCheck"
        />
      </SectionCard>

      <!-- 分布：最后入场，柱与扇区再各自错峰生长 -->
      <div class="dist-grid">
        <SectionCard
          class="reveal"
          :style="revealStyle(0, { base: 260 })"
          title="告警类型分布"
          :loading="isRefreshing"
        >
          <TypeDistChart v-if="typeDist.length" :data="typeDist" />
          <EmptyState v-else title="暂无数据" />
        </SectionCard>

        <SectionCard
          class="reveal"
          :style="revealStyle(1, { base: 260 })"
          title="严重级别分布"
          :loading="isRefreshing"
        >
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
import { revealStyle } from '../utils/motion'
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
/** 首屏数据是否已到位：到位后才把骨架换成数字（数字自己会滚动） */
const ready = ref(false)
const initialized = ref(false)

const days = computed(() => (timeRange.value === 'month' ? 30 : 7))

/**
 * 卡片由数据驱动生成，模板不再重复三遍；
 * 入场错峰交给 revealStyle(index)，不再是 CSS 里的 nth-child 硬编码。
 */
const statCards = computed(() => {
  const pending = stats.value.pendingAlerts
  return [
    {
      label: '今日登录',
      value: stats.value.todayLogins,
      icon: TrendCharts,
      tone: 'brand',
      hint: '按业务时区自然日统计',
    },
    {
      label: '待处理告警',
      value: pending,
      icon: Warning,
      tone: pending > 0 ? 'warning' : 'success',
      // 口径与告警列表的「待处理」筛选一致（status=pending 且未软删除）
      hint: pending > 0 ? '与告警列表「待处理」筛选一致' : '暂无待处理事项',
    },
    {
      label: '活跃用户',
      value: stats.value.activeUsers,
      icon: User,
      tone: 'info',
      hint: '今日有登录记录的账号',
    },
  ]
})

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
  ready.value = true
  initialized.value = true
}

const { loading, error, retryCooldown, execute } = useAsyncData(loadDashboard, {
  immediate: true,
})

// 切换时间范围防抖，避免快速连点打出多次请求
watch(days, debounce(() => execute(), 250))

/**
 * 刷新态：不再让整片内容变暗（旧实现是 opacity .62，观感"变灰"且与入场动画重叠），
 * 改为区块顶部的细进度条 + 数字自身平滑过渡到新值。
 */
const isRefreshing = computed(() => loading.value && initialized.value)
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 22px;
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

/* 入场动画由全局 .reveal 工具类承担（App.vue），
   延迟由 app/utils/motion.js 计算后以 --reveal-delay 注入，
   这里不再出现任何 nth-child 硬编码。 */

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 900px) {
  .dashboard,
  .stat-grid,
  .dist-grid {
    gap: 16px;
  }

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
