# Hello-FastApi

基于 FastAPI 框架的 RESTful API 服务，采用 DDD（领域驱动设计）架构和 RBAC 权限控制。

## 项目概述

本项目是一个高度模块化、可扩展的 API 服务系统，具有以下特性：

- **DDD 架构**：清晰的分层设计，业务领域与技术实现分离
- **RBAC 权限**：基于角色的访问控制，支持精细化权限管理
- **JWT 认证**：现代化的 Token 认证机制
- **异步处理**：全面支持 async/await，高性能并发处理
- **类型安全**：完整的类型提示，Pydantic 数据验证
- **代码复用**：公共验证器和仓储基类减少重复代码

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
├── docker/                     # Docker 配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── logs/                       # 日志目录
├── scripts/                    # 脚本文件
├── sql/                        # 数据库文件目录
├── src/                        # 源代码（所有业务代码）
│   ├── api/                    # API 接口层
│   ├── application/            # 应用层
│   │   ├── dto/                # 数据传输对象
│   │   ├── services
│   ├── domain/                 # 领域层
│   │   └── services/           # 应用服务
    │   │   ├── auth/               # 认证领域
    │   │   ├── department/         # 部门领域
    │   │   ├── log/                # 日志领域
    │   │   ├── menu/               # 菜单领域
    │   │   ├── rbac/               # RBAC 领域
    │   │   └── user/               # 用户领域
│   │   └── repositories/       # 仓储实现
│   │       ├── base.py         # 仓储基类
│   │       ├── department_repository.py
│   │       ├── log_repository.py
│   │       ├── menu_repository.py
│   │       ├── rbac_repository.py
│   │       └── user_repository.py
│   ├── infrastructure/         # 基础设施层
    │   ├── config/                 # 配置模块
    │   │   ├── __init__.py
    │   │   ├── asgi.py             # ASGI 入口
    │   │   └── settings.py         # 应用配置
│   │   ├── common.py           # 公共响应和转换工具
│   │   └── dependencies.py    # 依赖注入
│   │   ├── constants.py        # 常量定义
│   │   ├── decorators.py       # 装饰器
│   │   ├── exceptions.py       # 异常类
│   │   ├── logger.py           # 日志配置 (loguru)
│   │   ├── middlewares.py      # 中间件
│   │   ├── utils.py            # 工具函数
│   │   └── validators.py       # 公共验证器
│   │   ├── cache/              # 缓存实现
│   │   ├── database/           # 数据库实现
│   │   │   ├── connection.py
│   │   │   └── models.py       # ORM 模型
│   └── main.py                 # 应用入口
├── tests/                      # 测试代码
│   ├── integration/            # 集成测试
│   │   └── test_api.py         # API 集成测试
│   └── unit/                   # 单元测试
│       ├── test_auth.py        # 认证测试
│       ├── test_core.py        # 核心模块测试
│       ├── test_dto_validators.py # DTO 验证器测试
│       ├── test_user_service.py # 用户服务测试
│       └── test_validators.py  # 公共验证器测试
├── .env.example                # 环境变量模板
├── .env.development            # 开发环境配置
├── .env.production             # 生产环境配置
├── .env.testing                # 测试环境配置
├── .gitignore
├── pyproject.toml              # 项目配置
└── README.md
```
- 调用关系：接口层(api) → 应用层(application-services) → 领域层(domain-services)
- 基础设施层(infrastructure) 实现 领域层(domain) 定义的抽象接口（仓储、领域服务等），但 领域层不依赖基础设施层（依赖倒置原则）。
- 将项目中的 src目录下的所有文件清空，服务仍然可以启动，即基础设施不依赖任何src下的具体业务逻辑。

层级	职责
接口层	处理 HTTP 请求/响应，参数校验，认证授权，调用应用服务，返回结果。不包含业务逻辑。
应用层	编排用例：获取输入（DTO），调用领域对象，协调事务边界，调用仓储，发布领域事件。不包含核心业务规则。
领域层	核心业务逻辑：实体、值对象、聚合根、领域服务、仓储接口、领域事件。确保业务规则不变性。
基础设施层	技术实现：数据库访问（ORM）、外部服务调用、配置管理、日志等。实现领域层定义的抽象接口。


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
- 所有代码注释使用中文描述

### 代码检查

```bash
# Ruff 检查
ruff check . --fix
ruff format .

# MyPy 类型检查
mypy src/

# 运行测试
pytest

# 运行测试（带覆盖率）
pytest --cov=src --cov-report=term-missing
```

### 测试说明

项目包含完整的单元测试和集成测试：

**单元测试：**
- `test_validators.py`: 公共验证器测试
- `test_dto_validators.py`: DTO 验证器测试
- `test_user_service.py`: 用户服务测试
- `test_auth.py`: 认证服务测试
- `test_core.py`: 核心模块测试

**集成测试：**
- `test_api.py`: API 端点集成测试


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
