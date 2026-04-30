# Hello-FastApi

> 基于 Vue3 + FastAPI 的全栈中后台管理系统，前端基于 [Pure Admin](https://pure-admin.cn)，后端将 [pure-admin-backend](https://github.com/pure-admin/pure-admin-backend) 完整迁移至 Python FastAPI 框架，保持 API 接口、数据表结构、业务逻辑完全一致。

## 项目特色

- **JWT 双令牌认证** - Access Token + Refresh Token，支持无感刷新
- **RBAC 细粒度权限** - 基于角色的访问控制，支持按钮级权限
- **完整业务模块** - 用户管理、角色管理、权限管理、菜单管理
- **动态路由加载** - 后端返回菜单配置，前端动态生成路由
- **API 完全兼容** - 响应格式、路由前缀、权限编码与 pure-admin-backend 一致
- **Docker 一键部署** - FastAPI + PostgreSQL + Redis 完整技术栈
- **代码规范工具链** - ESLint、Prettier、Ruff、MyPy 完整配置

## 技术栈

### 后端 ([service/](service/))

| 技术 | 版本 | 说明 |
|-----|------|------|
| Python | >= 3.10 | 运行环境 |
| FastAPI | >= 0.115 | 异步 Web 框架 |
| SQLModel | >= 0.0.22 | ORM（SQLAlchemy 2.0 + Pydantic） |
| PostgreSQL | 16 | 生产数据库 |
| SQLite | - | 开发数据库 |
| Redis | 7 | 分布式缓存 |
| python-jose | >= 3.3.0 | JWT 认证 |
| bcrypt | >= 4.0.0 | 密码加密 |
| loguru | >= 0.7.0 | 日志管理 |
| Uvicorn | >= 0.30.0 | ASGI 服务器 |

### 前端 ([web/](web/))

| 技术 | 版本 | 说明 |
|-----|------|------|
| Node.js | >= 20.19 或 >= 22.13 | 运行环境 |
| pnpm | >= 9 | 包管理器 |
| Vue | 3.5+ | 渐进式前端框架 |
| Vite | 8+ | 构建工具 |
| TypeScript | 5.9+ | 类型安全 |
| Element Plus | 2.13+ | UI 组件库 |
| Pinia | 3.0+ | 状态管理 |
| TailwindCSS | 4+ | CSS 框架 |
| Axios | 1.13+ | HTTP 客户端 |
| vue-i18n | 11+ | 国际化 |
| ECharts | 6+ | 数据可视化 |

## 项目结构

```
Hello-FastApi/
├── service/                    # 后端服务（FastAPI）
│   ├── src/
│   │   ├── api/v1/            # API 路由层
│   │   ├── application/       # 应用层（DTO + Service）
│   │   ├── config/            # 配置管理
│   │   ├── core/              # 核心模块（中间件、异常、日志）
│   │   ├── domain/            # 领域层（实体模型）
│   │   ├── infrastructure/    # 基础设施层（数据库、缓存、仓储）
│   │   └── main.py            # 应用入口
│   ├── tests/                 # 测试代码
│   ├── docker/                # Docker 配置
│   ├── scripts/               # CLI 管理脚本
│   └── README.md              # 后端详细文档
│
└── web/                        # 前端项目（Vue3）
    ├── src/
    │   ├── api/               # API 调用
    │   ├── views/             # 页面组件
    │   ├── router/            # 路由配置
    │   ├── store/             # 状态管理
    │   ├── components/        # 公共组件
    │   └── utils/             # 工具函数
    ├── mock/                  # Mock 数据
    └── README.md              # 前端详细文档
```

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 20.19 或 >= 22.13
- pnpm >= 9
- Redis（可选，开发环境可不开启）
- Docker & Docker Compose（可选，用于容器化部署）

### 后端启动

详细说明请参考 [service/README.md](service/README.md)

```bash
cd service

# 方式一：使用脚本一键配置（推荐）
# Linux/Mac
bash scripts/setup_dev.sh
# Windows
scripts\setup_dev.bat

# 方式二：手动配置
uv venv --python 3.10
# Windows 激活
.venv\Scripts\activate
# Linux/Mac 激活
source .venv/bin/activate
uv pip install -e ".[dev]"

# 初始化数据库和管理员
python -m scripts.cli initdb
python -m scripts.cli createsuperuser
python -m scripts.cli seedrbac

# 启动开发服务器
python -m scripts.cli runserver
# API 文档：http://localhost:8000/api/system/docs
```

### 前端启动

详细说明请参考 [web/README.md](web/README.md)

```bash
cd web

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
# 访问地址：http://localhost:8848
```

## 前后端联调

| 配置项 | 后端 | 前端 |
|-------|------|------|
| 端口 | 8000 | 8848 |
| API 前缀 | /api/system | /api/system |
| 代理 | - | Vite proxy → localhost:8000 |
| CORS | 允许 localhost:8848 | - |

**联调步骤：**

1. 先启动后端服务（端口 8000）
2. 再启动前端服务（端口 8848）
3. 后端 CORS 已配置允许前端地址访问
4. 前端通过 Vite 代理请求后端 API

**请求流程：**
```
浏览器 → http://localhost:8848/api/system/xxx
       → Vite Proxy
       → http://localhost:8000/api/system/xxx
       → FastAPI 后端
```

## Docker 部署

### 一键启动

```bash
cd service/docker

# 启动所有服务（FastAPI + PostgreSQL + Redis）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 初始化数据库
docker-compose exec app python -m scripts.cli initdb
docker-compose exec app python -m scripts.cli createsuperuser
docker-compose exec app python -m scripts.cli seedrbac
```

### 服务端口

| 服务 | 端口 | 说明 |
|-----|------|------|
| FastAPI | 8000 | API 服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |

### 生产环境配置

修改 `service/.env.production`：

```bash
# 必须修改的配置
SECRET_KEY=your-secret-key-at-least-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-characters
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
CORS_ORIGINS=https://your-domain.com
```

## 环境变量

### 后端核心配置

| 变量名 | 默认值 | 说明 |
|-------|-------|------|
| APP_ENV | development | 运行环境（development/production/testing） |
| DATABASE_URL | sqlite+aiosqlite:///./sql/dev.db | 数据库连接字符串 |
| REDIS_URL | redis://localhost:6379/0 | Redis 连接字符串 |
| JWT_SECRET_KEY | - | JWT 密钥（生产环境必须修改） |
| SECRET_KEY | - | 应用密钥（生产环境必须修改） |
| JWT_ALGORITHM | HS256 | JWT 加密算法 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | 访问令牌有效期（分钟） |
| REFRESH_TOKEN_EXPIRE_DAYS | 7 | 刷新令牌有效期（天） |
| CORS_ORIGINS | http://localhost:8848,... | CORS 允许源（逗号分隔） |
| LOG_LEVEL | INFO | 日志级别 |

### 前端核心配置

| 变量名 | 默认值 | 说明 |
|-------|-------|------|
| VITE_PORT | 8848 | 开发服务器端口 |
| VITE_PUBLIC_PATH | / | 公共路径 |
| VITE_ROUTER_HISTORY | hash | 路由模式 |
| VITE_MOCK | false | 是否启用 Mock 数据 |

## API 接口概览

| 模块 | 前缀 | 主要接口 |
|------|------|---------|
| 认证 | /api/system | 登录、注册、登出、Token 刷新 |
| 用户 | /api/system/user | 用户 CRUD、批量删除、密码重置、状态切换 |
| 角色 | /api/system/role | 角色 CRUD、权限分配 |
| 权限 | /api/system/permission | 权限列表、创建、删除 |
| 菜单 | /api/system/menu | 菜单树、用户菜单、菜单 CRUD |

**统一响应格式：**

```json
{
  "code": 0,
  "message": "操作成功",
  "data": {}
}
```

**分页响应格式：**

```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "list": [],
    "total": 100,
    "pageSize": 10,
    "currentPage": 1
  }
}
```

## 修改记录

| 时间 | 修改人 | 主要修改内容 |
|------|--------|-------------|
| 2026-04-30 | Taowd | 重构 HTTP 限流模块：使用 SlowAPIMiddleware 全局中间件替代 @limiter.limit 装饰器；修复 slowapi 与 classy_fastapi 路由端点兼容性问题；增强限流中间件异常处理；清理 DEFAULT_LIMIT 常量及冗余导入 |
| 2026-04-26 09:38 | Taowd | 重构 .opencode 目录结构；agent-browser 技能迁移至 .opencode/skills；清理冗余配置文件 |
| 2026-04-26 09:33 | Taowd | 新增 .opencode 目录（含 code-gen、git-release 技能配置） |
| 2026-04-26 09:27 | Taowd | 新增 commit-changelog 提交记录 Skill；README.md 添加修改记录章节模板 |

## 开发规范

### 后端代码规范

```bash
cd service

# 代码检查
ruff check src/

# 代码格式化
ruff format src/

# 类型检查
mypy src/

# 运行测试
pytest

# 完整检查
ruff check src/ && ruff format src/ && mypy src/ && pytest
```

### 前端代码规范

```bash
cd web

# ESLint + Prettier + Stylelint
pnpm lint

# TypeScript 类型检查
pnpm typecheck

# 生产构建
pnpm build
```

### Git 提交规范

参考 [Angular 规范](https://github.com/conventional-changelog/conventional-changelog/tree/master/packages/conventional-changelog-angular)：

- `feat` 新功能
- `fix` 修复问题
- `docs` 文档更新
- `style` 代码格式
- `refactor` 重构
- `test` 测试相关
- `chore` 构建/工具

## 项目维护

### 数据库迁移

开发环境使用 SQLModel 自动创建表结构，生产环境建议使用 Alembic：

```bash
# 安装 Alembic
pip install alembic

# 初始化迁移
alembic init migrations

# 生成迁移脚本
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head
```

### 日志管理

日志文件位于 `service/logs/` 目录：
- `app.log` - 应用日志
- `access.log` - 访问日志
- `error.log` - 错误日志

### 备份策略

```bash
# SQLite 备份
cp service/sql/dev.db service/sql/dev.db.backup

# PostgreSQL 备份
docker-compose exec db pg_dump -U postgres hello_fastapi > backup.sql
```

## 许可证

[MIT License](LICENSE)

## 致谢

- [Pure Admin](https://pure-admin.cn) - 前端框架
- [pure-admin-backend](https://github.com/pure-admin/pure-admin-backend) - 后端逻辑参考
- [FastAPI](https://fastapi.tiangolo.com) - Python Web 框架
- [Element Plus](https://element-plus.org) - UI 组件库
