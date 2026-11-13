import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// 与 Vue 版 (web/) 对齐：/api 代理到同一套 FastAPI 后端
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": resolve(__dirname, "src") }
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: process.env.VITE_BACKEND_PORT
          ? `http://127.0.0.1:${process.env.VITE_BACKEND_PORT}`
          : "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  },
  build: {
    chunkSizeWarningLimit: 2000
  }
});
