# Task 1: Global CSS Theme Tokens + Google Fonts

## Goal

Add foundational frontend styling: Google Fonts in `index.html` and a complete global CSS theme in `App.vue`.

---

## 1. Google Fonts — `frontend/index.html`

Add these two `<link>` tags inside `<head>`, **before** the `<title>` tag:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+SC:wght@300;400;500;700&display=swap" rel="stylesheet" />
```

---

## 2. Global CSS — `frontend/src/App.vue`

Replace the entire `<style>` block with the following CSS. Copy it **verbatim**.

```css
/* ============================================================
   Global CSS Theme Tokens & Base Styles
   Campus Account Abnormal Login Monitoring & Alert Platform
   ============================================================ */

/* ---------- CSS Custom Properties (Theme Tokens) ---------- */
:root {
  /* Primary palette */
  --color-primary: #409eff;
  --color-primary-light: #66b1ff;
  --color-primary-lighter: #a0cfff;
  --color-primary-dark: #337ecc;
  --color-primary-darker: #2a6bb0;

  /* Semantic colors */
  --color-success: #67c23a;
  --color-warning: #e6a23c;
  --color-danger: #f56c6c;
  --color-info: #909399;

  /* Neutral / background */
  --color-bg-base: #f0f2f5;
  --color-bg-white: #ffffff;
  --color-bg-sidebar: #001529;
  --color-bg-sidebar-hover: #002140;
  --color-bg-card: #ffffff;

  /* Border */
  --color-border: #e4e7ed;
  --color-border-light: #ebeef5;

  /* Text */
  --color-text-primary: #303133;
  --color-text-regular: #606266;
  --color-text-secondary: #909399;
  --color-text-placeholder: #c0c4cc;
  --color-text-inverse: #ffffff;
  --color-text-sidebar: rgba(255, 255, 255, 0.65);

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 2px 8px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 4px 16px rgba(0, 0, 0, 0.1);

  /* Typography */
  --font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont,
    'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC',
    'Microsoft YaHei', sans-serif;
  --font-size-xs: 12px;
  --font-size-sm: 13px;
  --font-size-base: 14px;
  --font-size-lg: 16px;
  --font-size-xl: 18px;
  --font-size-2xl: 24px;
  --font-size-3xl: 32px;

  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 12px;
  --spacing-lg: 16px;
  --spacing-xl: 20px;
  --spacing-2xl: 24px;
  --spacing-3xl: 32px;

  /* Border radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;

  /* Transitions */
  --transition-fast: 0.2s ease;
  --transition-normal: 0.3s ease;
}

/* ---------- Reset / Base ---------- */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: var(--font-size-base);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  scroll-behavior: smooth;
}

body {
  font-family: var(--font-family);
  color: var(--color-text-primary);
  background-color: var(--color-bg-base);
  line-height: 1.6;
  min-height: 100vh;
}

a {
  color: var(--color-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--color-primary-light);
}

ul,
ol {
  list-style: none;
}

img {
  max-width: 100%;
  height: auto;
  display: block;
}

/* ---------- Scrollbar ---------- */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-placeholder);
}

/* ---------- Element Plus Overrides ---------- */
.el-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--color-border-light) !important;
  transition: box-shadow var(--transition-normal) !important;
}

.el-card:hover {
  box-shadow: var(--shadow-md) !important;
}

.el-table th.el-table__cell {
  background-color: var(--color-bg-base) !important;
  font-weight: 600 !important;
  color: var(--color-text-regular) !important;
}

.el-menu--vertical {
  border-right: none !important;
}

/* ---------- Utility Classes ---------- */
.text-center {
  text-align: center;
}

.text-right {
  text-align: right;
}

.text-primary {
  color: var(--color-primary);
}

.text-success {
  color: var(--color-success);
}

.text-warning {
  color: var(--color-warning);
}

.text-danger {
  color: var(--color-danger);
}

.text-info {
  color: var(--color-info);
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.mt-sm { margin-top: var(--spacing-sm); }
.mt-md { margin-top: var(--spacing-md); }
.mt-lg { margin-top: var(--spacing-lg); }
.mt-xl { margin-top: var(--spacing-xl); }
.mb-sm { margin-bottom: var(--spacing-sm); }
.mb-md { margin-bottom: var(--spacing-md); }
.mb-lg { margin-bottom: var(--spacing-lg); }
.mb-xl { margin-bottom: var(--spacing-xl); }
.p-sm { padding: var(--spacing-sm); }
.p-md { padding: var(--spacing-md); }
.p-lg { padding: var(--spacing-lg); }
.p-xl { padding: var(--spacing-xl); }
```

---

## Acceptance Criteria

1. `index.html` contains two `<link rel="preconnect">` tags and one `<link href="...">` tag for Google Fonts (Inter + Noto Sans SC).
2. `App.vue` exports the global CSS above.
3. `npm run dev` starts without errors.