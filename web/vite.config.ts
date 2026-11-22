import { getPluginsList } from "./build/plugins.ts";
import { include, exclude } from "./build/optimize.ts";
import { type UserConfigExport, type ConfigEnv, loadEnv } from "vite";
import {
  root,
  alias,
  wrapperEnv,
  pathResolve,
  __APP_INFO__
} from "./build/utils.ts";

export default async ({ mode }: ConfigEnv): Promise<UserConfigExport> => {
  const { VITE_CDN, VITE_PORT, VITE_COMPRESSION, VITE_PUBLIC_PATH } =
    wrapperEnv(loadEnv(mode, root));
  // 后端代理目标：默认 8000（显式 127.0.0.1，避免 localhost 解析到 ::1 命中其他 8000 绑定）。
  // 可用 VITE_BACKEND_PORT 覆盖——本机同时开发多个项目时，另一个服务可能已占用 8000。
  const backendPort = Number(process.env.VITE_BACKEND_PORT) || 8000;
  const backendTarget = `http://127.0.0.1:${backendPort}`;
  return {
    base: VITE_PUBLIC_PATH,
    root,
    resolve: {
      alias
    },
    // 服务端渲染
    server: {
      // 端口号
      port: VITE_PORT,
      host: "0.0.0.0",
      // 本地跨域代理 https://cn.vitejs.dev/config/server-options.html#server-proxy
      proxy: {
        "/api": {
          // 代理到后端 FastAPI 服务（含 WebSocket：实时消息推送）
          target: backendTarget,
          changeOrigin: true,
          ws: true
        },
        "/media": {
          // 上传静态资源（头像等）代理到后端
          target: backendTarget,
          changeOrigin: true
        }
      },
      // 预热文件以提前转换和缓存结果，降低启动期间的初始页面加载时长并防止转换瀑布
      warmup: {
        clientFiles: ["./index.html", "./src/{views,components}/*"]
      }
    },
    plugins: await getPluginsList(VITE_CDN, VITE_COMPRESSION),
    // https://cn.vitejs.dev/config/dep-optimization-options.html#dep-optimization-options
    optimizeDeps: {
      include,
      exclude
    },
    build: {
      // https://cn.vitejs.dev/guide/build.html#browser-compatibility
      target: "es2015",
      sourcemap: false,
      // 警告阈值回落到 1500KB：暴露超大 chunk 而不是用 4000 掩盖问题
      // （univer 相关 chunk 仍会超阈值告警，属预期——它只被 example-data 页按需加载）
      chunkSizeWarningLimit: 1500,
      rolldownOptions: {
        input: {
          index: pathResolve("./index.html", import.meta.url)
        },
        // 静态资源分类打包
        output: {
          chunkFileNames: "static/js/[name]-[hash].js",
          entryFileNames: "static/js/[name]-[hash].js",
          assetFileNames: "static/[ext]/[name]-[hash].[ext]",
          /*
           * 手动分包（rolldown advancedChunks，见 rolldown 1.2 类型定义
           * OutputOptions.advancedChunks: { groups?: CodeSplittingGroup[] }）：
           * 把四个大块依赖各自拆成独立 vendor chunk，业务代码更新时
           * 这些不变的 vendor 长缓存不受影响；echarts/univer 均为按需
           * 动态加载，不进首屏。
           */
          advancedChunks: {
            groups: [
              {
                name: "element-plus",
                // element-plus 本体 + 其内部依赖（@element-plus/icons-vue 等）
                test: /[\\/]node_modules[\\/](element-plus|@element-plus)[\\/]/
              },
              {
                name: "echarts",
                // echarts + 底层 zrender（现为 welcome 图表按需动态加载）
                test: /[\\/]node_modules[\\/](echarts|zrender)[\\/]/
              },
              {
                name: "univer",
                // 电子表格全家桶（仅 example-data 页异步子组件加载）。
                //
                // includeDependenciesRecursively 必须关掉、test 用函数而非
                // 宽泛正则：@univerjs 内部有大量"按需动态 import"的语言资源
                // （engine-render 连字断词 patterns，约 7.4MB + 各包 locale
                // 目录），页面只用 zh-CN。若一律并入 univer 组会把主 chunk
                // 从约 6.9MB 撑到 11MB+，劣化 example-data 页加载；排除后
                // rolldown 会按原样为它们生成独立按需 chunk。
                includeDependenciesRecursively: false,
                test: id => {
                  const p = id.replace(/\\/g, "/");
                  if (!p.includes("/node_modules/@univerjs/")) return false;
                  // 各包 locale 目录（lib/locale、locales）
                  if (/\/locales?\//.test(p)) return false;
                  // engine-render 连字断词 patterns：<lang>-<hash>.js
                  // （lib/es/ 与 lib/ 两种产物形态，动态 import 的独立资源）
                  if (
                    /\/@univerjs\/engine-render\/lib\/(es\/)?[a-z]{2,3}(-[0-9A-Za-z]+)*-[A-Za-z0-9_-]{8}\.js$/.test(
                      p
                    )
                  ) {
                    return false;
                  }
                  return true;
                }
              },
              {
                name: "vue-vendor",
                // vue 全家桶：vue 内核(@vue/*)、路由、状态、组合式工具、pureadmin 工具
                test: /[\\/]node_modules[\\/](@vue|vue|vue-router|pinia|@vueuse|@pureadmin)[\\/]/
              }
            ]
          }
        },
        checks: {
          pluginTimings: false,
          toleratedTransform: false
        }
      }
    },
    define: {
      __INTLIFY_PROD_DEVTOOLS__: false,
      __APP_INFO__: JSON.stringify(__APP_INFO__)
    }
  };
};
