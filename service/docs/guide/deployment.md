# 部署

本文档介绍如何将后端服务部署到不同环境，包括 Docker 容器化部署和生产环境部署。

[← 返回首页](../../README.md)

---

## Docker 部署

### 前置条件

- 安装 Docker 和 Docker Compose

### 启动服务

```bash
cd docker
docker-compose up -d
```

### 初始化数据库

容器启动后，执行数据库初始化命令：

```bash
# 创建数据库表
docker-compose exec app python -m scripts.cli initdb

# 初始化 RBAC 数据
docker-compose exec app python -m scripts.cli seedrbac

# 创建超级管理员
docker-compose exec app python -m scripts.cli createsuperuser
```

### Docker 配置说明

Docker 配置文件位于 `docker/` 目录：

- 后端镜像基于 `python:3.10-slim`
- 使用 Uvicorn 运行，默认 4 个 Worker
- 服务监听端口：8000

### 常用 Docker 命令

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down

# 重建并启动
docker-compose up -d --build
```

---

## 生产环境部署

### 使用 Gunicorn + Uvicorn Worker

生产环境推荐使用 Gunicorn 作为进程管理器，配合 Uvicorn Worker：

```bash
gunicorn src.config.asgi:application \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  -b 0.0.0.0:8000
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-w 4` | Worker 进程数，建议设为 CPU 核心数 × 2 + 1 |
| `-k uvicorn.workers.UvicornWorker` | 使用 Uvicorn 的异步 Worker |
| `-b 0.0.0.0:8000` | 绑定地址和端口 |

### 环境变量

生产环境需设置以下环境变量：

```bash
export APP_ENV=production
```

或通过 `.env.production` 文件配置，确保数据库连接指向生产 PostgreSQL 实例。

---

## 反向代理（Nginx）

生产环境通常在 Gunicorn 前面加一层 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/docs {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

---

## 健康检查

服务启动后，可通过以下方式检查服务状态：

- 访问 Swagger UI：`http://your-domain/api/docs`
- 查看应用日志：`logs/` 目录下的日志文件

---

## 数据库迁移

生产环境数据库变更需谨慎操作：

1. 备份生产数据库
2. 在测试环境验证变更
3. 执行数据库迁移或 `initdb`（仅限新表创建）
4. 验证服务正常运行
