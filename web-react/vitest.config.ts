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
  },
});
