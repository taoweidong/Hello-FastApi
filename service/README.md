# Hello-FastApi 后端服务

基于 FastAPI 框架的 RESTful API 服务，采用 DDD（领域驱动设计）架构，支持 JWT 双令牌认证和 RBAC 权限控制。

## 项目概述

本项目是 Vue3 + FastAPI 全栈中后台管理系统的后端服务，具有以下特性：

- **DDD 架构**：清晰的四层设计（api/application/domain/infrastructure）
- **JWT 双令牌**：Access Token + Refresh Token 认证机制
- **RBAC 权限**：基于角色的细粒度权限控制
- **异步处理**：全面支持 async/await，高性能并发
- **类型安全**：完整的类型提示，Pydantic V2 数据验证

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | FastAPI ≥0.115 |
| ORM | SQLModel ≥0.0.22 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) |
| 异步驱动 | aiosqlite / asyncpg |
| 缓存 | Redis ≥5.0 |
| 认证 | JWT (python-jose) |
| 验证 | Pydantic V2 |
| 日志 | Loguru |
| 服务器 | Uvicorn |

## 目录结构

```
service/
├── docker/                     # Docker 配置
├── docs/                       # 文档目录
├── logs/                       # 日志目录
├── scripts/                    # 脚本工具
│   ├── cli.py                  # 管理命令行工具
│   ├── setup_dev.sh            # 开发环境安装脚本 (Linux/Mac)
│   ├── setup_dev.bat           # 开发环境安装脚本 (Windows)
│   └── verify_api.py           # API 验证脚本
├── sql/                        # 数据库文件目录
├── src/                        # 源代码
│   ├── api/                    # 接口层：HTTP 请求处理、认证授权
│   │   ├── v1/                 # API v1 版本路由
│   │   ├── common.py           # 公共响应工具
│   │   └── dependencies.py     # 依赖注入
│   ├── application/            # 应用层：用例编排、DTO 定义
│   │   ├── dto/                # 数据传输对象
│   │   └── services/           # 应用服务
│   ├── config/                 # 配置模块
│   │   ├── asgi.py             # ASGI 入口
│   │   └── settings.py         # 应用配置
│   ├── core/                   # 核心模块
│   │   ├── constants.py        # 常量定义
│   │   ├── exceptions.py       # 异常类
│   │   ├── logger.py           # 日志配置
│   │   ├── middlewares.py      # 中间件
│   │   ├── utils.py            # 工具函数
│   │   └── validators.py       # 公共验证器
│   ├── domain/                 # 领域层：核心业务逻辑
│   │   ├── entities/           # 领域实体
│   │   ├── repositories/       # 仓储接口（抽象）
│   │   └── services/           # 领域服务
│   ├── infrastructure/         # 基础设施层：技术实现
│   │   ├── cache/              # 缓存实现
│   │   ├── database/           # 数据库相关
│   │   └── repositories/       # 仓储实现
│   └── main.py                 # 应用入口
├── tests/                      # 测试代码
│   ├── integration/            # 集成测试
│   └── unit/                   # 单元测试
├── .env.development            # 开发环境配置
├── .env.production             # 生产环境配置
├── .env.testing                # 测试环境配置
└── pyproject.toml              # 项目配置
```

## 快速开始

### 环境要求

- Python ≥ 3.10
- UV（推荐的 Python 包管理工具）

### 安装步骤

**方式一：使用安装脚本（推荐）**

Linux/Mac:
```bash
bash scripts/setup_dev.sh
```

Windows:
```cmd
scripts\setup_dev.bat
```

**方式二：手动安装**

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

### 数据库初始化

按以下顺序执行命令完成数据库初始化：

```bash
# 1. 创建数据库表
python -m scripts.cli initdb

# 2. 初始化 RBAC 数据（角色、权限）
python -m scripts.cli seedrbac

# 3. 初始化测试数据（菜单、日志等）
python -m scripts.cli seeddata

# 4. 创建超级管理员
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
```

### 启动服务

```bash
python -m scripts.cli runserver
```

服务启动后访问：
- API 文档: http://localhost:8000/api/docs
- ReDoc 文档: http://localhost:8000/api/redoc

## 管理命令

通过 `python -m scripts.cli` 执行管理命令：

| 命令 | 说明 |
|------|------|
| `runserver` | 启动开发服务器（默认端口 8000） |
| `initdb` | 初始化数据库表 |
| `seedrbac` | 初始化默认角色和权限数据 |
| `seeddata` | 初始化测试数据（菜单、登录日志、操作日志、系统日志） |
| `createsuperuser` | 创建超级管理员 |

**createsuperuser 参数：**
```bash
python -m scripts.cli createsuperuser --username <用户名> --email <邮箱> --password <密码> [--nickname <昵称>]
# 简写形式
python -m scripts.cli createsuperuser -u <用户名> -e <邮箱> -p <密码> [-n <昵称>]
```

## 环境配置

项目支持多环境配置，通过 `APP_ENV` 环境变量切换：

| 环境 | 配置文件 | 说明 |
|------|----------|------|
| development | `.env.development` | 开发环境，DEBUG=true，使用 SQLite |
| production | `.env.production` | 生产环境，DEBUG=false，使用 PostgreSQL |
| testing | `.env.testing` | 测试环境，使用测试数据库 |

### 切换环境

Linux/Mac:
```bash
export APP_ENV=production
python -m scripts.cli runserver
```

Windows:
```cmd
set APP_ENV=production
python -m scripts.cli runserver
```

### 配置加载顺序

```
系统环境变量 > .env.{APP_ENV} > .env > 默认值
```

## 开发规范

### 代码风格

- 遵循 PEP 8 规范
- 使用 Ruff 进行代码格式化和检查
- **所有代码注释使用中文描述**
- 所有公共接口使用类型提示

### 数据库规范

- **表名前缀**：所有数据表以 `sys_` 为前缀
- **主键格式**：`id` 字段使用 36 位 UUID 字符串

### 代码检查

```bash
# Ruff 检查和格式化
ruff check . --fix
ruff format .

# MyPy 类型检查
mypy src/

# 运行测试
pytest

# 运行测试（带覆盖率）
pytest --cov=src --cov-report=term-missing
```

## 部署

### Docker 部署

```bash
cd docker
docker-compose up -d
```

### 生产环境

使用 Gunicorn + Uvicorn Worker 部署：

```bash
gunicorn src.config.asgi:application -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 许可证

MIT License
