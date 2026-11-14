import { defineConfig } from 'vitest/config';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  resolve: {
    // 对齐 UmiJS 的 @ → src 别名（Umi 构建自带，vitest 需显式声明）
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  test: {
    // 页面运行时依赖 window/localStorage/navigator，统一用 happy-dom 模拟
    environment: 'happy-dom',
    include: ['src/**/*.test.{ts,tsx}'],
    // app.test 首个用例需动态 import('./app')，其依赖链（pro-components/antd-style/dayjs）
    // 冷启动转换较慢，5s 默认值容易在 CI 冷缓存下超时
    testTimeout: 20000,
  },
});
