# Hello-FastApi

基于 FastAPI 框架的 RESTful API 服务，采用 DDD（领域驱动设计）架构和 RBAC 权限控制。

## 项目概述

本项目是一个高度模块化、可扩展的 API 服务系统，具有以下特性：

- **DDD 架构**：清晰的分层设计，业务领域与技术实现分离
- **RBAC 权限**：基于角色的访问控制，支持精细化权限管理
- **JWT 认证**：现代化的 Token 认证机制
- **异步处理**：全面支持 async/await，高性能并发处理
- **类型安全**：完整的类型提示，Pydantic 数据验证

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | FastAPI |
| ORM | SQLAlchemy 2.0+ (AsyncIO) |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 缓存 | Redis |
| 认证 | JWT (python-jose) |
| 验证 | Pydantic |
| 日志 | Loguru |

## 目录结构

```
Hello-FastApi/
├── docs/                       # 文档目录
│   ├── api/                    # API 文档
│   └── design/                 # 设计文档
├── docker/                     # Docker 配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── logs/                       # 日志目录
│   ├── app.log                 # 应用日志
│   ├── access.log              # 访问日志
│   └── error.log               # 错误日志
├── scripts/                    # 脚本文件
│   ├── lint.sh
│   ├── setup_dev.bat
│   ├── setup_dev.sh
│   └── verify_api.py
├── sql/                        # 数据库文件目录
│   ├── dev.db                  # 开发数据库
│   └── test.db                 # 测试数据库
├── src/                        # 源代码（所有业务代码）
│   ├── api/                    # API 接口层
│   │   ├── v1/                 # V1 版本接口
│   │   │   ├── auth_routes.py  # 认证路由
│   │   │   ├── rbac_routes.py  # RBAC 路由
│   │   │   └── user_routes.py  # 用户路由
│   │   ├── common.py
│   │   └── dependencies.py
│   ├── application/            # 应用层
│   │   ├── dto/                # 数据传输对象
│   │   └── services/           # 应用服务
│   ├── config/                 # 配置模块
│   │   ├── __init__.py
│   │   ├── asgi.py             # ASGI 入口
│   │   └── settings.py         # 应用配置
│   ├── core/                   # 核心模块
│   │   ├── constants.py
│   │   ├── decorators.py
│   │   ├── exceptions.py
│   │   ├── logger.py           # 日志配置 (loguru)
│   │   ├── middlewares.py
│   │   ├── utils.py
│   │   └── validators.py
│   ├── domain/                 # 领域层
│   │   ├── auth/               # 认证领域
│   │   ├── rbac/               # RBAC 领域
│   │   └── user/               # 用户领域
│   ├── infrastructure/         # 基础设施层
│   │   ├── cache/              # 缓存实现
│   │   ├── database/           # 数据库实现
│   │   │   ├── connection.py
│   │   │   └── models.py       # ORM 模型
│   │   └── repositories/       # 仓储实现
│   └── main.py                 # 应用入口
├── tests/                      # 测试代码
│   ├── integration/            # 集成测试
│   └── unit/                   # 单元测试
├── .env.example                # 环境变量模板
├── .env.development            # 开发环境配置
├── .env.production             # 生产环境配置
├── .env.testing                # 测试环境配置
├── .gitignore
├── pyproject.toml              # 项目配置
└── README.md
```

## 快速开始

### 环境要求

- Python >= 3.10
- UV（Python 包管理工具）

### 安装步骤

**Linux/Mac:**
```bash
bash scripts/setup_dev.sh
```

**Windows:**
```cmd
scripts\setup_dev.bat
```

### 手动安装

```bash
# 安装 UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv --python 3.10

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 启动服务

```bash
python -m scripts.cli runserver
```

服务启动后访问：
- API 文档: http://localhost:8000/api/docs
- ReDoc 文档: http://localhost:8000/api/redoc

## 环境配置

项目支持多环境配置，通过 `APP_ENV` 环境变量切换：

| 环境 | 配置文件 | 说明 |
|------|----------|------|
| development | `.env.development` | 开发环境，DEBUG=true，详细日志 |
| production | `.env.production` | 生产环境，DEBUG=false，精简日志 |
| testing | `.env.testing` | 测试环境，使用测试数据库 |

### 配置加载顺序

```
系统环境变量 > .env.{APP_ENV} > .env > 默认值
```

### 切换环境

**Linux/Mac:**
```bash
export APP_ENV=production
python -m scripts.cli runserver
```

**Windows:**
```cmd
set APP_ENV=production
python -m scripts.cli runserver
```

### 创建本地配置

```bash
# 复制模板创建本地配置
cp .env.example .env

# 编辑配置
vim .env
```

## 管理命令

```bash
python -m scripts.cli runserver       # 启动开发服务器
python -m scripts.cli createsuperuser # 创建超级用户
python -m scripts.cli initdb          # 初始化数据库
python -m scripts.cli seedrbac        # 填充 RBAC 初始数据
```

## 开发规范

### 代码风格

- 遵循 PEP 8 规范
- 使用 Ruff 进行代码格式化和检查
- 所有公共接口使用类型提示

### 代码检查

```bash
# Ruff 检查
ruff check . --fix
ruff format .

# MyPy 类型检查
mypy src/

# 运行测试
pytest
```

## API 概览

### 认证接口

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/refresh | 刷新令牌 |

### 用户接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/users | 获取用户列表 |
| POST | /api/v1/users | 创建用户 |
| GET | /api/v1/users/{id} | 获取用户详情 |
| PUT | /api/v1/users/{id} | 更新用户 |
| DELETE | /api/v1/users/{id} | 删除用户 |

### RBAC 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/v1/roles | 获取角色列表 |
| POST | /api/v1/roles | 创建角色 |
| GET | /api/v1/permissions | 获取权限列表 |
| POST | /api/v1/permissions | 创建权限 |

## 部署

### Docker 部署

```bash
docker-compose up -d
```

### 生产环境

使用 Gunicorn + Nginx 部署：

```bash
gunicorn src.config.asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 许可证

MIT License
