# P0 基础设施完善设计文档

> 日期：2026-04-30
> 范围：service/ 后端服务
> 包含：Alembic 迁移、限流中间件、Docker Compose、Jenkins CI/CD

---

## 一、P0-1: Alembic 数据库迁移

### 1.1 架构

```
service/
├── alembic/
│   ├── versions/           # 迁移脚本
│   ├── env.py              # Alembic 环境配置（async 适配）
│   └── alembic.ini         # Alembic 主配置
├── scripts/
│   └── cli.py              # 扩展 migrate/rollback 命令
└── .env.*                  # 各环境 DATABASE_URL 配置
```

### 1.2 关键设计

- **Async Engine 适配**：`env.py` 使用 `asyncio.run()` + `create_async_engine` 处理异步迁移
- **SQLModel Metadata**：从 `src.infrastructure.database.models` 导入所有模型，使用 `SQLModel.metadata`
- **初始迁移**：先 `alembic revision --autogenerate -m "initial_schema"` 从现有表结构生成
- **CLI 扩展**：在 `scripts/cli.py` 添加 `migrate`（执行 upgrade）和 `rollback`（执行 downgrade）子命令
- **多环境支持**：`alembic.ini` 中 `sqlalchemy.url` 设为占位符，实际值从 `.env` 环境变量读取

### 1.3 数据流

```
cli migrate → 读取 .env → 加载 alembic.ini → env.py 创建 async engine → 对比 models.metadata → 生成/执行 SQL
```

### 1.4 风险与缓解

- **现有 SQLite 数据迁移**：开发环境用 `sqlite:///sql/dev.db`，首次迁移需处理已存在表。使用 `--autogenerate` 检测差异，手动调整迁移脚本
- **多数据库方言**：SQLite（开发）和 PostgreSQL（生产）DDL 不同。迁移脚本需测试两种方言

---

## 二、P0-2: 限流中间件

### 2.1 架构

复用已有的 `slowapi` 库（已在 `main.py` 注册 `SlowAPIMiddleware` 和 `RateLimitExceeded` handler），只需完善后端配置。

### 2.2 关键设计

- **限流后端**：`SlowAPI` 默认使用内存存储，改为 `Redis` 存储以支持多 worker 分布式限流
- **限流维度**：
  - 按 IP：全局默认限流（从 `.env` 读取 `RATE_LIMIT_TIMES` / `RATE_LIMIT_SECONDS`）
  - 按用户：认证用户单独限流（基于 user_id）
- **白名单**：超级管理员 IP 和用户 ID 不限流
- **降级策略**：Redis 不可用时自动降级为内存限流
- **响应格式**：限流触发时返回统一 JSON 格式 `{code: 429, msg: "请求过于频繁", data: null, retry_after: X}`

### 2.3 配置项

```env
RATE_LIMIT_TIMES=100          # 时间窗口内最大请求数
RATE_LIMIT_SECONDS=60         # 时间窗口（秒）
RATE_LIMIT_WHITELIST_IPS=     # 逗号分隔的 IP 白名单
RATE_LIMIT_STORAGE=redis      # redis 或 memory
```

### 2.4 数据流

```
请求 → IPFilterMiddleware → RateLimiter → 检查 Redis counter → 超限返回 429 → 通过则进入路由
```

---

## 三、P0-3: Docker Compose 补全

### 3.1 架构

```yaml
services:
  app:     # FastAPI 应用（已有，需增强）
  db:      # PostgreSQL 15（新增）
  redis:   # Redis 7（新增）
```

### 3.2 关键设计

- **app 服务**：
  - 构建上下文指向 `service/`
  - 环境变量从 `.env.production` 注入
  - 依赖 `db` 和 `redis` 服务就绪
  - 健康检查：`curl -f http://localhost:8000/health`
- **db 服务**：
  - 镜像：`postgres:15-alpine`
  - 数据卷：`pgdata:/var/lib/postgresql/data`
  - 环境变量：`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
  - 健康检查：`pg_isready`
- **redis 服务**：
  - 镜像：`redis:7-alpine`
  - 数据卷：`redisdata:/data`
  - 健康检查：`redis-cli ping`
- **网络**：自定义 bridge 网络 `hello-fastapi-net`

### 3.3 环境变量映射

| .env 变量 | Docker 注入 |
|-----------|-------------|
| DATABASE_URL | `postgresql+asyncpg://user:pass@db:5432/hello_fastapi` |
| REDIS_URL | `redis://redis:6379/0` |
| SECRET_KEY | 从宿主机 `.env` 注入 |
| ENVIRONMENT | `production` |

---

## 四、P0-4: Jenkins CI/CD Pipeline

### 4.1 架构

```
Jenkinsfile (Declarative Pipeline)
├── Agent: Docker (python:3.10-slim)
├── Stages:
│   ├── Checkout
│   ├── Lint (ruff)
│   ├── Typecheck (mypy)
│   ├── Test (pytest + coverage)
│   ├── Build Docker Image
│   └── Deploy (可选，按环境)
└── Post:
    ├── 邮件通知
    └── 构建产物归档
```

### 4.2 关键设计

- **触发方式**：
  - Git Webhook（push 到 main/develop 分支）
  - 手动触发（Jenkins UI）
  - 定时触发（每日凌晨全量测试）
- **参数化构建**：
  - `DEPLOY_ENV`: dev / staging / prod
  - `RUN_TESTS`: true / false
- **Docker 构建**：多阶段构建，生产镜像最小化
- **部署策略**：
  - dev: 直接 docker-compose up
  - staging/prod: 推送镜像到私有仓库，远程服务器拉取部署
- **通知**：构建成功/失败发送企业微信或邮件通知

### 4.3 Pipeline 结构

```groovy
pipeline {
    agent { docker { image 'python:3.10-slim' } }
    parameters { choice(name: 'DEPLOY_ENV', choices: ['dev', 'staging', 'prod']) }
    stages {
        stage('Checkout') { ... }
        stage('Lint') { sh 'ruff check src/' }
        stage('Typecheck') { sh 'mypy src/' }
        stage('Test') { sh 'pytest tests/ --cov=src --cov-fail-under=80' }
        stage('Build') { sh 'docker build -t hello-fastapi:${BUILD_NUMBER} .' }
        stage('Deploy') { when { expression { params.DEPLOY_ENV != 'dev' } } ... }
    }
    post { always { mail notification } }
}
```

### 4.4 目录结构

```
service/
├── Jenkinsfile              # 主 Pipeline 文件
├── docker/
│   ├── Dockerfile           # 生产镜像（多阶段）
│   ├── docker-compose.yml   # 补全后的编排
│   └── Jenkins/
│       └── deploy.sh        # 部署辅助脚本
```

---

## 五、执行顺序与依赖

```
P0-1 (Alembic) ──┐
                 ├── 互相独立，可并行开发
P0-2 (限流)    ──┤
                 ├── 依赖 P0-3（需要 Docker 中的 Redis/DB 服务）
P0-3 (Docker)  ──┘
                 │
P0-4 (Jenkins) ── 依赖 P0-1~P0-3 完成后验证
```

推荐执行顺序：**P0-1 → P0-2 → P0-3 → P0-4**

---

## 六、验收标准

| 任务 | 验收条件 |
|------|----------|
| P0-1 | `alembic upgrade head` 成功创建所有表；`alembic downgrade base` 成功清空 |
| P0-2 | 超过限流阈值返回 429；Redis 降级为 memory 时仍正常工作 |
| P0-3 | `docker-compose up -d` 后三个服务全部健康；`/health` 端点返回 200 |
| P0-4 | Jenkins Pipeline 可手动触发成功；lint/test/build 全部通过 |
