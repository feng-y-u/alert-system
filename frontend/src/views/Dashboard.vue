<template>
  <el-container class="dashboard-container">
    <el-header>
      <h1>校园账号异常登录监测平台</h1>
    </el-header>
    <el-main>
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>今日登录</template>
            <div class="card-value">0</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>异常告警</template>
            <div class="card-value warning">0</div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <template #header>活跃用户</template>
            <div class="card-value">0</div>
          </el-card>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style scoped>
.dashboard-container {
  height: 100vh;
}

.el-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
}

.el-header h1 {
  font-size: 20px;
}

.el-main {
  background-color: #f5f5f5;
  padding: 20px;
}

.card-value {
  font-size: 36px;
  font-weight: bold;
  text-align: center;
  color: #409eff;
}

.card-value.warning {
  color: #e6a23c;
}
</style>
