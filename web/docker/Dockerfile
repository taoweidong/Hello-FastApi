# 前端生产环境 Dockerfile
# 多阶段构建：build-stage 编译 Vue 项目 → production-stage 用 Nginx 托管静态资源

# ── 构建阶段 ──
FROM node:20-alpine AS build-stage

WORKDIR /app

# 启用 corepack 并激活 pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# 使用国内镜像加速（按需移除）
RUN npm config set registry https://registry.npmmirror.com

# 先复制依赖文件，利用 Docker 缓存层
COPY .npmrc package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# 复制源码并构建生产环境产物
COPY . .
RUN pnpm build

# ── 生产阶段 ──
FROM nginx:stable-alpine AS production-stage

# 安装 Brotli 动态模块（支持 .br 预压缩文件）
RUN apk add --no-cache nginx-mod-http-brotli

# 替换默认配置
RUN rm /etc/nginx/conf.d/default.conf

# 在 Nginx 主配置顶部加载 Brotli 模块（load_module 必须在 main 上下文）
RUN sed -i '1i\load_module modules/ngx_http_brotli_filter_module.so;\nload_module modules/ngx_http_brotli_static_module.so;' /etc/nginx/nginx.conf

# 复制自定义 Nginx 配置
COPY docker/nginx.conf /etc/nginx/conf.d/app.conf

# 从构建阶段复制产物
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 创建非 root 用户运行 nginx
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
