import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 后端地址：默认与 README 的本地开发端口一致（8001）。
// 若改跑 Docker 后端（8000），用环境变量覆盖，无需改文件：
//   VITE_DEV_PROXY_TARGET=http://localhost:8000 npm run dev
// （此前硬编码 8000 与文档的 8001 不一致，导致 5173 上所有 /api 请求打空，
//   见 docs/tech/14-评估与改进.md P1-7）
const target = process.env.VITE_DEV_PROXY_TARGET || 'http://localhost:8001'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 注意：/api/notifications 必须排在 /api 之前，且关闭缓冲，
      // 否则 SSE 会被普通代理规则吞掉，前端永远收不到实时告警
      '/api/notifications': {
        target,
        changeOrigin: true,
        ws: false,
        headers: { 'Connection': 'keep-alive' },
      },
      '/api': {
        target,
        changeOrigin: true,
      },
    },
  },
})
