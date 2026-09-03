<template>
  <section class="section-card">
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
})
</script>

<style scoped>
.section-card {
  background: var(--bg-surface);
  border-radius: var(--r-lg);
  box-shadow: var(--shadow-sm);
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
</style>
