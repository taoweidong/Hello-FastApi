/**
 * @name 代理配置：/api → 本地 FastAPI 后端（与 Vue 版一致）
 */
export default {
  dev: {
    '/api/': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
    },
  },
};
