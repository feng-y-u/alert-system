<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">今日登录</span>
          <div class="stat-badge success">
            <el-icon><TrendCharts /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ formatNumber(stats.todayLogins) }}</div>
        <div class="stat-footer">
          <span class="stat-trend positive">+12%</span>
          <span class="stat-compare">较昨日</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">待处理告警</span>
          <div class="stat-badge warning">
            <el-icon><Warning /></el-icon>
          </div>
        </div>
        <div class="stat-value" :class="{ 'text-warning': stats.pendingAlerts > 0 }">
          {{ stats.pendingAlerts }}
        </div>
        <div class="stat-footer">
          <span class="stat-trend" :class="stats.pendingAlerts > 10 ? 'negative' : 'neutral'">
            {{ stats.pendingAlerts > 10 ? '↑' : '→' }}
          </span>
          <span class="stat-compare">需关注</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <span class="stat-label">活跃用户</span>
          <div class="stat-badge info">
            <el-icon><User /></el-icon>
          </div>
        </div>
        <div class="stat-value">{{ formatNumber(stats.activeUsers) }}</div>
        <div class="stat-footer">
          <span class="stat-trend positive">+5%</span>
          <span class="stat-compare">较昨日</span>
        </div>
      </div>
    </div>

    <!-- 图表区域 -->
    <div class="chart-section">
      <div class="section-header">
        <h2 class="section-title">登录趋势</h2>
        <div class="section-actions">
          <el-radio-group v-model="timeRange" size="small">
            <el-radio-button label="week">近7天</el-radio-button>
            <el-radio-button label="month">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div ref="chartRef" class="chart-container"></div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <h3 class="section-title">快捷操作</h3>
      <div class="actions-grid">
        <button class="action-card" disabled>
          <div class="action-icon">
            <el-icon><Document /></el-icon>
          </div>
          <span class="action-label">查看日志</span>
        </button>
        <button class="action-card" disabled>
          <div class="action-icon">
            <el-icon><WarningFilled /></el-icon>
          </div>
          <span class="action-label">处理告警</span>
        </button>
        <button class="action-card" @click="refreshData">
          <div class="action-icon primary">
            <el-icon><Refresh /></el-icon>
          </div>
          <span class="action-label">刷新数据</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'
import api from '../api'
import {
  TrendCharts,
  Warning,
  User,
  Document,
  WarningFilled,
  Refresh
} from '@element-plus/icons-vue'

const stats = reactive({
  todayLogins: 0,
  pendingAlerts: 0,
  activeUsers: 0,
})

const trend = ref([])
const timeRange = ref('week')
const chartRef = ref(null)
let chartInstance = null

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN')
}

const refreshData = async () => {
  try {
    const days = timeRange.value === 'week' ? 7 : 30
    const res = await api.get('/api/stats', { params: { days } })
    stats.todayLogins = res.todayLogins
    stats.pendingAlerts = res.pendingAlerts
    stats.activeUsers = res.activeUsers
    trend.value = res.loginTrend || []

    if (chartInstance) {
      chartInstance.setOption({
        xAxis: {
          data: trend.value.map(t => t.date),
        },
        series: [{
          data: trend.value.map(t => t.count),
        }],
      })
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

onMounted(async () => {
  await refreshData()

  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#e5e7eb',
        borderWidth: 1,
        textStyle: {
          color: '#111827',
        },
        padding: [12, 16],
      },
      grid: {
        left: 0,
        right: 0,
        top: 20,
        bottom: 0,
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: trend.value.map(t => t.date),
        axisLine: {
          lineStyle: { color: '#e5e7eb' },
        },
        axisTick: { show: false },
        axisLabel: {
          color: '#6b7280',
          fontSize: 12,
        },
      },
      yAxis: {
        type: 'value',
        splitLine: {
          lineStyle: {
            color: '#f3f4f6',
            type: 'dashed',
          },
        },
        axisLabel: {
          color: '#6b7280',
          fontSize: 12,
        },
      },
      series: [
        {
          type: 'line',
          data: trend.value.map(t => t.count),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#111827',
          },
          itemStyle: {
            color: '#111827',
            borderWidth: 2,
            borderColor: '#fff',
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(17, 24, 39, 0.1)' },
                { offset: 1, color: 'rgba(17, 24, 39, 0)' },
              ],
            },
          },
        },
      ],
    })
  }

  // 监听 timeRange 变化，自动刷新数据
  watch(timeRange, () => {
    refreshData()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* === 统计卡片 === */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.stat-card {
  background: var(--color-bg-elevated);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.stat-badge {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-badge.success {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.stat-badge.warning {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-badge.info {
  background-color: #dbeafe;
  color: #3b82f6;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
  margin-bottom: 12px;
}

.stat-value.text-warning {
  color: var(--color-warning);
}

.stat-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-trend {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}

.stat-trend.positive {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.stat-trend.negative {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.stat-trend.neutral {
  background-color: var(--color-border-light);
  color: var(--color-text-secondary);
}

.stat-compare {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* === 图表区域 === */
.chart-section {
  background: var(--color-bg-elevated);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.chart-container {
  height: 320px;
}

/* === 快捷操作 === */
.quick-actions {
  margin-top: 8px;
}

.quick-actions .section-title {
  margin-bottom: 16px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover:not(:disabled) {
  border-color: var(--color-primary);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.action-card:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background-color: var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--color-text-secondary);
}

.action-icon.primary {
  background-color: var(--color-primary);
  color: white;
}

.action-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>