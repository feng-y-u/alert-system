<template>
  <div class="dashboard" v-loading="loading">
    <!-- 错误状态 -->
    <div v-if="error" class="error-placeholder">
      <p>数据加载失败，请稍后重试</p>
      <el-button type="primary" @click="refreshData">重试</el-button>
    </div>

    <template v-else>
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

      <!-- 登录趋势 -->
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">登录趋势</h2>
          <div class="section-actions">
            <el-radio-group v-model="timeRange" size="small">
              <el-radio-button value="week">近7天</el-radio-button>
              <el-radio-button value="month">近30天</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <LoginTrendChart v-if="trend.length > 0" :data="trend" />
        <div v-else class="empty-chart">暂无登录数据</div>
      </div>

      <!-- 告警趋势 -->
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">告警趋势</h2>
        </div>
        <AlertTrendChart v-if="alertTrend.length > 0" :data="alertTrend" />
        <div v-else class="empty-chart">暂无告警数据</div>
      </div>

      <div class="alert-charts-grid">
        <div class="chart-section">
          <div class="section-header">
            <h2 class="section-title">告警类型分布</h2>
          </div>
          <TypeDistChart v-if="typeDist.length > 0" :data="typeDist" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>

        <div class="chart-section">
          <div class="section-header">
            <h2 class="section-title">严重级别分布</h2>
          </div>
          <SeverityDistChart v-if="severityDist.length > 0" :data="severityDist" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>
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
    </template>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { debounce } from 'lodash-es'
import api from '../api'
import { getAlertStats } from '../api/stats'
import LoginTrendChart from '../components/charts/LoginTrendChart.vue'
import AlertTrendChart from '../components/charts/AlertTrendChart.vue'
import TypeDistChart from '../components/charts/TypeDistChart.vue'
import SeverityDistChart from '../components/charts/SeverityDistChart.vue'
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
const alertTrend = ref([])
const typeDist = ref([])
const severityDist = ref([])
const timeRange = ref('week')
const loading = ref(false)
const error = ref(false)

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN')
}

const refreshData = async () => {
  loading.value = true
  error.value = false
  try {
    const days = timeRange.value === 'week' ? 7 : 30
    const [loginRes, alertRes] = await Promise.all([
      api.get('/api/stats', { params: { days } }),
      getAlertStats(days),
    ])
    stats.todayLogins = loginRes.todayLogins
    stats.pendingAlerts = loginRes.pendingAlerts
    stats.activeUsers = loginRes.activeUsers
    trend.value = loginRes.loginTrend || []
    alertTrend.value = alertRes.alertTrend || []
    typeDist.value = alertRes.typeDist || []
    severityDist.value = alertRes.severityDist || []
  } catch (err) {
    console.error('Failed to load stats:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const debouncedRefresh = debounce(refreshData, 300)

onMounted(() => {
  refreshData()
})

watch(timeRange, () => {
  debouncedRefresh()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* === 错误占位 === */
.error-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 0;
}

.error-placeholder p {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* === 空图表占位 === */
.empty-chart {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 14px;
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

/* === 告警图表区 === */
.alert-charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
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
  .alert-charts-grid {
    grid-template-columns: 1fr;
  }

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
