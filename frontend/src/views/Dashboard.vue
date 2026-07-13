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
            <el-radio-button value="week">近7天</el-radio-button>
            <el-radio-button value="month">近30天</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <div ref="chartRef" class="chart-container"></div>
    </div>

    <!-- 告警分析区 -->
    <div class="chart-section">
      <div class="section-header">
        <h2 class="section-title">告警趋势</h2>
      </div>
      <div ref="alertTrendRef" class="chart-container"></div>
    </div>

    <div class="alert-charts-grid">
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">告警类型分布</h2>
        </div>
        <div ref="typeDistRef" class="chart-container-small"></div>
      </div>

      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">严重级别分布</h2>
        </div>
        <div ref="severityDistRef" class="chart-container-small"></div>
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
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import * as echarts from 'echarts'
import api from '../api'
import { getAlertStats } from '../api/stats'
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
const alertTrend = ref([])
const typeDist = ref([])
const severityDist = ref([])

const alertTrendRef = ref(null)
const typeDistRef = ref(null)
const severityDistRef = ref(null)
let chartInstance = null
let alertTrendChart = null
let typeDistChart = null
let severityDistChart = null

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN')
}

const refreshData = async () => {
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

    // 销毁所有旧图表
    chartInstance?.dispose()
    alertTrendChart?.dispose()
    typeDistChart?.dispose()
    severityDistChart?.dispose()
    chartInstance = null
    alertTrendChart = null
    typeDistChart = null
    severityDistChart = null

    // 登录趋势图（保留现有逻辑，不动！）
    if (chartRef.value) {
      chartRef.value.style.opacity = '0'
      chartInstance = echarts.init(chartRef.value)
      chartInstance.setOption({
        animationDuration: 2500,
        animationEasing: 'cubicOut',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#111827' },
          padding: [12, 16],
        },
        grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: trend.value.map(t => t.date),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        series: [{
          type: 'line',
          data: trend.value.map(t => t.count),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          animationDuration: 2500,
          animationEasing: 'cubicOut',
          animationDelay: 400,
          lineStyle: {
            width: 3,
            color: '#111827',
            shadowColor: 'rgba(17, 24, 39, 0.3)',
            shadowBlur: 10,
            shadowOffsetY: 5,
          },
          itemStyle: { color: '#111827', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            opacity: 0.8,
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(17, 24, 39, 0.2)' },
                { offset: 1, color: 'rgba(17, 24, 39, 0)' },
              ],
            },
          },
        }],
      })
      requestAnimationFrame(() => {
        chartRef.value.style.opacity = '1'
      })
    }

    // === BEGIN NEW CODE: 告警趋势折线图 ===
    if (alertTrendRef.value) {
      alertTrendChart = echarts.init(alertTrendRef.value)
      alertTrendChart.setOption({
        animationDuration: 2500,
        animationEasing: 'cubicOut',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#111827' },
          padding: [12, 16],
        },
        grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: alertTrend.value.map(t => t.date),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        series: [{
          type: 'line',
          data: alertTrend.value.map(t => t.count),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#F59E0B',
            shadowColor: 'rgba(245, 158, 11, 0.3)',
            shadowBlur: 10,
            shadowOffsetY: 5,
          },
          itemStyle: { color: '#F59E0B', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            opacity: 0.8,
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(245, 158, 11, 0.2)' },
                { offset: 1, color: 'rgba(245, 158, 11, 0)' },
              ],
            },
          },
        }],
      })
    }

    // === 告警类型分布环形图 ===
    if (typeDistRef.value) {
      typeDistChart = echarts.init(typeDistRef.value)
      const typeNameMap = { frequency: '频率异常', device: '设备异常' }
      typeDistChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, textStyle: { color: '#6b7280', fontSize: 12 } },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          label: { show: false },
          labelLine: { show: false },
          data: typeDist.value.map((item, i) => ({
            name: typeNameMap[item.name] || item.name,
            value: item.value,
            itemStyle: { color: ['#111827', '#F59E0B'][i % 2] },
          })),
        }],
      })
    }

    // === 严重级别分布柱状图 ===
    if (severityDistRef.value) {
      severityDistChart = echarts.init(severityDistRef.value)
      const severityNameMap = { low: '低', medium: '中', high: '高' }
      const severityColorMap = { low: '#3B82F6', medium: '#F59E0B', high: '#EF4444' }
      severityDistChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: severityDist.value.map(s => severityNameMap[s.name] || s.name),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        series: [{
          type: 'bar',
          data: severityDist.value.map(s => ({
            value: s.value,
            itemStyle: { color: severityColorMap[s.name] || '#111827' },
          })),
          barWidth: '40%',
          itemStyle: { borderRadius: [6, 6, 0, 0] },
        }],
      })
    }
    // === END NEW CODE ===
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

onMounted(async () => {
  await refreshData()

  // 监听 timeRange 变化
  watch(timeRange, () => {
    refreshData()
  })
})

onUnmounted(() => {
  chartInstance?.dispose()
  alertTrendChart?.dispose()
  typeDistChart?.dispose()
  severityDistChart?.dispose()
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
  transition: opacity 0.8s ease;
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

/* === 告警图表区 === */
.alert-charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-container-small {
  height: 280px;
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