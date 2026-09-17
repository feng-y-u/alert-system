<template>
  <section class="section-card" :aria-busy="loading ? 'true' : 'false'">
    <!-- 数据刷新时的细进度条：比整片置灰更克制，也不遮挡内容 -->
    <span v-if="loading" class="section-card__progress" aria-hidden="true" />

    <header v-if="title || $slots.actions" class="section-card__head">
      <div class="section-card__titles">
        <h2 class="section-card__title">{{ title }}</h2>
        <p v-if="subtitle" class="section-card__subtitle">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.actions" class="section-card__actions">
        <slot name="actions" />
      </div>
    </header>
    <div class="section-card__body" :class="{ 'section-card__body--flush': flush }">
      <slot />
    </div>
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  /** 去掉内边距，让表格等内容贴边铺满 */
  flush: { type: Boolean, default: false },
  /** 数据刷新中：顶部细进度条 + aria-busy */
  loading: { type: Boolean, default: false },
})
</script>

<style scoped>
.section-card {
  position: relative;
  background: var(--bg-surface);
  border: 1px solid transparent;
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  /* 区块卡的反馈层级低于统计卡：只做描边与阴影，不做位移 */
  transition:
    box-shadow var(--motion-base) var(--ease-standard),
    border-color var(--motion-base) var(--ease-standard);
}

.section-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-soft);
}

.section-card__progress {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  transform-origin: left center;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--brand-500) 45%,
    var(--brand-600) 60%,
    transparent 100%
  );
  animation: section-progress 1.1s var(--ease-standard) infinite;
}

@keyframes section-progress {
  0% {
    transform: scaleX(0.1);
    opacity: 0.25;
  }
  55% {
    transform: scaleX(0.7);
    opacity: 1;
  }
  100% {
    transform: scaleX(1);
    opacity: 0.15;
  }
}

.section-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-bottom: 1px solid var(--border-soft);
}

.section-card__titles {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.section-card__title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-strong);
  letter-spacing: -0.01em;
}

.section-card__subtitle {
  font-size: 13px;
  color: var(--text-faint);
}

.section-card__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.section-card__body {
  padding: 22px;
}

/* 表格类内容不需要内边距，让表格贴边更好看 */
.section-card__body--flush {
  padding: 0;
}

@media (prefers-reduced-motion: reduce) {
  /* 不做扫动，改为静态细条：仍然表达"正在更新"，但不产生动态 */
  .section-card__progress {
    animation: none;
    transform: scaleX(1);
    opacity: 0.35;
  }
}
</style>
