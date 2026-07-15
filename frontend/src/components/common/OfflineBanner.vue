<template>
  <Transition name="banner">
    <div v-if="!isOnline" class="offline-banner">
      <el-icon><WarningFilled /></el-icon>
      <span>网络连接已断开，部分功能不可用</span>
    </div>
    <div v-else-if="showReconnected" class="online-banner">
      <el-icon><CircleCheckFilled /></el-icon>
      <span>网络已恢复</span>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { WarningFilled, CircleCheckFilled } from '@element-plus/icons-vue'

const props = defineProps({
  isOnline: { type: Boolean, required: true },
  wasOffline: { type: Boolean, default: false },
})

const emit = defineEmits(['reconnected'])
const showReconnected = ref(false)

watch(
  () => props.isOnline,
  (val, old) => {
    if (val && !old && props.wasOffline) {
      showReconnected.value = true
      emit('reconnected')
      setTimeout(() => {
        showReconnected.value = false
      }, 3000)
    }
  }
)
</script>

<style scoped>
.offline-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: var(--color-danger);
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.online-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 16px;
  background-color: var(--color-success);
  color: white;
  font-size: 14px;
  font-weight: 500;
}

.banner-enter-active,
.banner-leave-active {
  transition: transform 0.3s ease;
}

.banner-enter-from,
.banner-leave-to {
  transform: translateY(-100%);
}
</style>
