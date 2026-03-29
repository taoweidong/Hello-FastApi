# Hello-FastApi

> 基于 Vue3 + FastAPI 的全栈中后台管理系统，前端基于 [Pure Admin](https://pure-admin.cn) 框架，后端将 [pure-admin-backend](https://github.com/pure-admin/pure-admin-backend)（Node.js）完整迁移至 Python FastAPI 框架，保持 API 接口、数据表结构、业务逻辑完全一致。

## 项目简介

这是一个前后端分离的中后台管理系统，旨在提供一个完整的 RBAC 权限管理解决方案。

- **后端**：使用 FastAPI 框架，采用 DDD（领域驱动设计）架构，实现 RBAC 细粒度权限管理
- **前端**：基于 Vue3 + Vite + Element-Plus + TypeScript + Pinia + TailwindCSS 构建
- **API 一致性**：与 pure-admin-backend 保持完全一致的响应格式、路由前缀、字段命名、权限编码和数据模型
- **参考文档**：前端参考 [Pure Admin](https://pure-admin.cn/pages/introduction/)，后端参考 [pure-admin-backend](https://github.com/pure-admin/pure-admin-backend)

## 功能特性

- JWT 令牌认证 + Token 自动刷新
- RBAC 细粒度角色权限管理
- 用户管理（CRUD、批量操作、状态切换、密码重置）
- 角色管理（CRUD、权限分配）
- 权限管理
- 菜单管理（树形结构、动态路由）
- 国际化支持（中英文）
- Docker 一键部署
- 完善的代码规范工具链（ESLint、Prettier、Stylelint、Ruff、MyPy）

## 技术栈

### 后端（service/）

| 技术 | 说明 |
|-----|------|
| FastAPI >=0.115 | 异步 Web 框架 |
| SQLModel >=0.0.22 | ORM（基于 SQLAlchemy 2.0） |
| Pydantic Settings | 配置管理 |
| python-jose | JWT 认证 |
| bcrypt | 密码加密 |
| loguru | 日志管理 |
| Redis | 分布式缓存 |
| SQLite（开发）/ PostgreSQL（生产） | 数据库 |
| Uvicorn | ASGI 服务器 |
| Python >=3.10 | 运行环境 |

### 前端（web/）

| 技术 | 说明 |
|-----|------|
| Vue 3.5+ | 渐进式前端框架 |
| Vite 8+ | 构建工具 |
| TypeScript 5.9+ | 类型安全 |
| Element Plus | UI 组件库 |
| Pinia | 状态管理 |
| TailwindCSS 4 | CSS 框架 |
| Axios | HTTP 客户端 |
| vue-i18n | 国际化 |
| ECharts 6 | 数据可视化 |
| Node >=20.19 / >=22.13 | 运行环境 |
| pnpm >=9 | 包管理器 |

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
│   └── pyproject.toml
└── web/                        # 前端（Vue3 Pure Admin）
    ├── src/
    │   ├── api/               # API 调用
    │   ├── views/             # 页面组件
    │   ├── router/            # 路由配置
    │   ├── store/             # 状态管理
    │   ├── components/        # 公共组件
    │   ├── utils/             # 工具函数
    │   └── layout/            # 布局组件
    ├── mock/                  # Mock 数据
    └── package.json
```

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 20.19 或 >= 22.13
- pnpm >= 9
- Redis（可选，开发环境可不开启）

### 后端启动

```bash
cd service

# 方式一：使用脚本一键配置（推荐）
# Linux/Mac
bash scripts/setup_dev.sh
# Windows
scripts\setup_dev.bat

# 方式二：手动配置
uv venv --python 3.10
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
uv pip install -e ".[dev]"

# 初始化数据库
python -m scripts.cli initdb

# 创建超级管理员
python -m scripts.cli createsuperuser

# 初始化 RBAC 数据（角色和权限）
python -m scripts.cli seedrbac

# 启动开发服务器
python -m scripts.cli runserver
# API 文档：http://localhost:8000/api/system/docs
```

### 前端启动

```bash
cd web

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
# 访问地址：http://localhost:8848
```

### 前后端联调

1. 先启动后端服务（端口 8000）
2. 再启动前端服务（端口 8848）
3. 后端 CORS 已配置允许前端开发地址访问
4. 前端通过 axios 直接请求后端 API（http://localhost:8000/api/system/...）

## API 接口概览

| 模块 | 前缀 | 主要接口 |
|------|------|---------|
| 认证 | /api/system | 登录、注册、登出、Token 刷新 |
| 用户 | /api/system/user | 用户 CRUD、批量删除、密码重置、状态切换 |
| 角色 | /api/system/role | 角色 CRUD、权限分配 |
| 权限 | /api/system/permission | 权限列表、创建、删除 |
| 菜单 | /api/system/menu | 菜单树、用户菜单、菜单 CRUD |

统一响应格式：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

## 数据库设计

核心数据表：

- **users** - 用户表
- **roles** - 角色表
- **permissions** - 权限表
- **user_roles** - 用户-角色关联表
- **role_permissions** - 角色-权限关联表
- **menus** - 菜单表
- **ip_rules** - IP 规则表

默认角色：admin（系统管理员）、user（普通用户）、moderator（审核员）

## Docker 部署

```bash
cd service/docker

# 启动所有服务（FastAPI + PostgreSQL + Redis）
docker-compose up -d

# 初始化数据库和数据
docker-compose exec app python -m scripts.cli initdb
docker-compose exec app python -m scripts.cli createsuperuser
docker-compose exec app python -m scripts.cli seedrbac
```

服务端口：

- API 服务：8000
- PostgreSQL：5432
- Redis：6379

## 环境变量

后端核心配置（.env 文件）：

| 变量名 | 默认值 | 说明 |
|-------|-------|------|
| APP_ENV | development | 运行环境 |
| DATABASE_URL | sqlite+aiosqlite:///./sql/dev.db | 数据库连接 |
| REDIS_URL | redis://localhost:6379/0 | Redis 连接 |
| JWT_SECRET_KEY | - | JWT 密钥（需设置） |
| SECRET_KEY | - | 应用密钥（需设置） |
| CORS_ORIGINS | http://localhost:3000,... | CORS 允许源 |

详细配置参考 `service/.env.example`

## 开发指南

### 后端代码规范

```bash
cd service
ruff check src/          # 代码检查
ruff format src/         # 代码格式化
mypy src/                # 类型检查
pytest                   # 运行测试
```

### 前端代码规范

```bash
cd web
pnpm lint                # ESLint + Prettier + Stylelint
pnpm typecheck           # TypeScript 类型检查
pnpm build               # 生产构建
```

## 许可证

[MIT License](LICENSE)

## 致谢

- [Pure Admin](https://pure-admin.cn) - 前端框架
- [pure-admin-backend](https://github.com/pure-admin/pure-admin-backend) - 后端逻辑参考
- [FastAPI](https://fastapi.tiangolo.com) - Python Web 框架
