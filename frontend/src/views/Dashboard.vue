<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>今日登录</template>
          <div class="card-value">{{ stats.todayLogins }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>异常告警</template>
          <div class="card-value warning">{{ stats.pendingAlerts }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>活跃用户</template>
          <div class="card-value">{{ stats.activeUsers }}</div>
        </el-card>
      </el-col>
    </el-row>
    <el-card class="chart-card" shadow="hover">
      <template #header>登录趋势</template>
      <div ref="chartRef" class="chart"></div>
    </el-card>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'

const stats = reactive({
  todayLogins: 0,
  pendingAlerts: 0,
  activeUsers: 0,
})

const chartRef = ref(null)
let chartInstance = null

onMounted(() => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
      yAxis: { type: 'value' },
      series: [
        {
          type: 'line',
          data: [0, 0, 0, 0, 0, 0, 0],
          smooth: true,
          areaStyle: { opacity: 0.15 },
        },
      ],
    })
  }
})

onUnmounted(() => {
  chartInstance?.dispose()
})
</script>

<style scoped>
.card-value {
  font-size: 36px;
  font-weight: bold;
  text-align: center;
  color: #409eff;
}
.card-value.warning {
  color: #e6a23c;
}
.chart-card {
  margin-top: 20px;
}
.chart {
  height: 300px;
}
</style>