import { resolve } from "path";
import vueJsx from "@vitejs/plugin-vue-jsx";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [vueJsx()],
  resolve: {
    alias: {
      "@": resolve(__dirname, "src"),
      "@build": resolve(__dirname, "build")
    }
  },
  test: {
    // happy-dom：轻量 DOM 环境，覆盖 composables 与纯逻辑单测足够
    environment: "happy-dom",
    globals: true,
    include: ["src/**/__tests__/**/*.{spec,test}.{ts,tsx}"],
    // 单测必须可独立重复执行：不共享状态、不依赖执行顺序
    sequence: {
      concurrent: false
    }
  }
});
