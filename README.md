# Hello-FastApi 系统设计文档（基于UV管理 & DDD & RBAC架构）

---

## 1. 项目概述

**项目名称**：FastApi  
**功能描述**：基于 FastApi 框架，结合 JWT 与 RBAC 权限认证机制，采用领域驱动设计（DDD）架构，打造高度模块化与可扩展的 API 服务系统。  
本系统重点支持权限精细化控制、多版本管理（UV管理）、API限流、黑白名单等功能，大幅提升系统可用性和健壮性，最大限度减少代码重复，提升系统可维护性和业务扩展能力。  
系统设计充分考虑AI开发的便利性，采用标准化的模块结构和清晰的依赖关系，便于AI助手进行代码生成和系统构建。

---

## 2. 设计目标

- 基于 **DDD** 架构，清晰划分业务领域与技术实现分层。
- 引入 **RBAC**（基于角色的访问控制）认证授权，增强权限管理灵活度。
- 采用 **UV管理**，单元版本化，支持模块独立演进。
- 目录结构合理规划，避免代码冗余，提高复用率, 引入ruff mypy等工具提升项目的规范性和一致性
- 结合 FastApi 提供高性能、高类型安全的 REST API。
- 支持 JWT 认证，满足现代前后端分离业务需求。
- 实现API限流、黑白名单等安全防护机制。
- 使用FastApi生态成熟插件，提升系统健壮性, 减少重复代码。
- 实现高可用性、高性能、可监控的系统架构。
- **AI友好设计**：标准化模块结构，便于AI助手开发和维护。

---

## 3. 技术架构

### 3.1 技术栈

| 层级       | 技术/工具                             | 说明                              |
|------------|--------------------------------------|-----------------------------------|
| 开发语言   | Python 3.10+                        | 稳定主流Python版本                |
| API框架    | FastAPI                    | 类型安全、高性能API框架            |
| 认证       | FastAPI Users | 这是一个完整的“用户系统”解决方案。它不仅仅是一个库，而是一套可扩展的系统，内置了注册、登录、重置密码、OAuth2 集成（Google, GitHub 等）以及 JWT/cookie 会话管理。          |
| 限流       | pydantic-settings    | 它利用 Pydantic 的强大验证能力来管理环境变量和 .env 文件。                   |
|docs      | Scalar                      | 2025-2026 年新兴的文档 UI，比 Swagger UI 更现代、加载更快、交互更流畅。FastAPI 可以通过挂载静态文件或中间件轻松集成 Scalar。                  |
| ORM        | SQLAlchemy (2.0+) + AsyncIO:                       | SQLAlchemy 2.0 彻底重构了对异步的支持，配合 asyncpg (PostgreSQL) 或 aiomysql，能充分发挥 FastAPI 的异步性能。                     |
| 缓存       | Redis                            | 高性能内存缓存                    |
| 数据库     | PostgreSQL                      | 关系型数据库，支持事务与高并发    |
| 版本管理   | UV管理                          | 单元模块版本管理                     |
| 设计模式   | DDD（领域驱动设计）               | 业务复杂系统拆分和设计指导          |
| 容器化     | Docker                           | 容器化部署                        |
| 安全防护   | django-cors-headersdjango-defenderdjango-securitydjango-ratelimit | 多层安全防护 |

FastAPI-Limiter:通过简单的装饰器实现速率限制功能，防止 API 滥用。它还支持 WebSocket 的速率限制，非常适合需要保护资源的场景。
FastAPI-Cache:用于缓存管理的插件，支持 Redis、Memcache 和 AWS DynamoDB 等缓存后端，能够缓存 API 响应和函数结果，提升性能。
FastAPI-Mail:一个轻量级的邮件发送库，支持文本和附件邮件的发送，并内置后台任务管理功能，适合需要邮件通知的应用场景。
FastAPI-pagination:该插件用于实现分页功能，允许开发者轻松从 API 路由返回分页响应，而无需手动编写分页逻辑。它非常适合需要处理大量数据的场景。
FastAPI-Admin:为 FastAPI 提供类似 Django 管理界面的插件，基于 Bootstrap 模板构建，适合需要快速实现管理后台的项目。


最佳实践：https://github.com/zhanymkanov/fastapi-best-practices?spm=a2c6h.12873639.article-detail.11.26dc6ab5F4AgPX

实现功能时现在最佳实践库 https://github.com/zhanymkanov/fastapi-best-practices?spm=a2c6h.12873639.article-detail.11.26dc6ab5F4AgPX  中查询，如果有对应的库可复用，即引入使用
---

## 4. 领域驱动设计（DDD）架构解析

### 4.1 分层说明

| 层级           | 职责描述                              |
|----------------|-------------------------------------|
| 接口层(API层)  | 提供REST API接口，调用应用层逻辑，处理HTTP请求响应 |
| 应用层         | 负责编排业务流程，协调领域层服务和基础设施 |
| 领域层         | 业务核心，包含实体(Entity)、值对象(Value Object)、聚合根(Aggregate Root)、领域服务 |
| 基础设施层     | 数据库访问、认证、外部服务接口实现、缓存管理 |

### 4.2 业务领域划分（核心领域）

| 领域            | 主要功能                                 |
|-----------------|--------------------------------------|
| 用户管理域(User)| 用户注册、信息维护、JWT登录认证、个人资料管理 |
| 权限管理域(RBAC)| 角色管理、权限分配、访问控制、权限验证 |
| 认证域(Auth)    | JWT 生成、验证与刷新、会话管理、安全控制 |
| 通用服务域(Core)| 通用的工具函数、中间件、异常处理、配置管理 |
| 业务服务域(Business)| 具体业务逻辑处理，如订单、商品、支付等 |
| 安全域(Security)| API限流、IP黑白名单、安全防护、攻击检测 |

### 4.3 领域模型设计原则

- **聚合根**：每个聚合都有唯一的聚合根，负责维护聚合内的一致性
- **值对象**：不可变对象，用于描述实体的属性特征
- **领域服务**：处理跨实体的业务逻辑
- **仓储模式**：抽象数据访问逻辑，实现领域与基础设施解耦

---

## 5. AI友好的目录结构（结合UV & DDD）

```plaintext
FastApi/
├── docker/
│   ├── Dockerfile                 # 应用容器构建文件
│   └── docker-compose.yml         # 服务编排配置
├── src/
│   ├── api/                      # API接口层（Django-Ninja路由及视图）
│   │   ├── v1/                   # 版本控制 - v1版本
│   │   └── common.py             # API公共组件 - AI可直接实现
│   ├── application/              # 应用层
│   │   ├── services/             # 应用服务 - AI可直接实现
│   │   │   ├── user_service.py   # 用户领域服务
│   │   ├── dto/                  # 数据传输对象 - AI可直接实现
│   │   │   └── security_dto.py   # 安全DTO
│   │   └── interfaces/           # 应用层接口定义 - AI可直接实现
│   │       └── base_service.py
│   ├── domain/                   # 领域层（实体、聚合根、领域服务、仓储接口）
│   ├── infrastructure/           # 基础设施层
│   │   ├── repositories/         # 仓储实现 - AI可直接实现
│   ├── core/                     # 通用功能模块 - AI可直接实现
│   │   ├── exceptions.py         # 自定义异常
│   │   ├── middlewares.py        # 中间件
│   │   ├── decorators.py         # 装饰器
│   │   ├── validators.py         # 验证器
│   │   ├── utils.py              # 工具函数
│   │   ├── constants.py          # 常量定义
│   │   └── logger.py             # 日志配置
│   └── tests/                    # 测试代码 - AI可直接实现
│       ├── unit/                 # 单元测试
│       ├── integration/          # 集成测试
│       └── fixtures/             # 测试数据
├── config/                       # 配置文件 - AI可直接实现
│   ├── settings/                 # 配置文件
│   │   ├── base.py               # 基础配置
│   │   ├── development.py        # 开发环境配置
│   │   ├── production.py         # 生产环境配置
│   │   └── testing.py            # 测试环境配置
│   ├── urls.py                   # 路由汇总 - AI可直接实现
│   ├── asgi.py
│   └── wsgi.py
├── scripts/                      # 脚本文件 - AI可直接实现
│   ├── migrate.sh                # 数据库迁移脚本
│   ├── deploy.sh                 # 部署脚本
│   └── backup.sh                 # 备份脚本
├── logs/                         # 日志文件目录
│   ├── app.log                   # 应用日志
│   ├── error.log                 # 错误日志
│   └── access.log                # 访问日志
├── docs/                         # 文档
│   ├── api_docs/                 # API文档
│   └── design_docs/              # 设计文档
├── .env.example                  # 环境变量示例
├── .gitignore
├── requirements.txt              # 依赖包列表 - AI可直接实现
├── requirements-dev.txt          # 开发依赖 - AI可直接实现
├── manage.py                     # Django管理脚本 - AI可直接实现
└── README.md                     # 项目说明 - AI可直接实现
```

---

## 6. 开发规范

### 6.1 代码规范
- **代码风格**: 符合 PEP 8 规范，使用 Ruff 自动格式化
- **类型提示**: 所有公共接口使用类型提示，使用 MyPy 检查
- **文档字符串**: 使用 Google 风格 docstring
- **代码质量**: Ruff 0 错误，MyPy 宽松模式通过

### 6.2 测试规范
- **测试框架**: pytest + pytest-django
- **测试覆盖**: 核心业务逻辑覆盖率 ≥ 80%
- **测试类型**: 单元测试、集成测试
- **测试配置**: `pyproject.toml`

### 6.3 Git 工作流
- **分支模型**: Git Flow
  - `main`: 生产环境分支
  - `develop`: 开发主分支
  - `feature/*`: 功能开发分支
  - `bugfix/*`: 缺陷修复分支
  - `hotfix/*`: 紧急修复分支
- **提交信息**: 语义化提交（feat/fix/docs/refactor/test/chore）

## 12. 部署架构

支持多种部署方式：
- **开发环境**: Docker Compose 一键启动
- **生产环境**: Gunicorn + Nginx + PostgreSQL + Redis
- **容器化**: Docker + Kubernetes

---

---

## 19. 快速开始

### 19.1 环境要求

- Python >= 3.10.11
- UV（Python包管理工具）
- SQLite（开发环境）或 PostgreSQL（生产环境）
- Redis（缓存，可选）

### 19.2 本地环境搭建

#### 方式一：自动化安装脚本（推荐）

**Linux/Mac:**
```bash
# 运行安装脚本
bash scripts/setup_dev.sh
```

**Windows:**
```cmd
# 运行安装脚本
scripts\setup_dev.bat
```

脚本将自动完成以下操作：
1. 检查并安装 UV
2. 创建 Python 虚拟环境（Python 3.10.11）
3. 安装项目依赖
4. 代码格式化和检查
5. 创建数据库表
6. 创建初始管理员账号
7. 运行单元测试

#### 方式二：手动安装

```bash
# 1. 安装 UV（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/Mac
# 或 PowerShell（Windows）
# irm https://astral.sh/uv/install.ps1 | iex

# 2. 创建虚拟环境
uv venv --python 3.10.11

# 3. 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate.bat  # Windows

# 4. 安装项目依赖（包含开发依赖）
uv pip install -e ".[dev]"


```

### 19.3 服务启动

```bash
# 激活虚拟环境后启动服务
python manage.py runserver

# 指定端口

```

服务启动后，访问：
- API根路径: http://localhost:8000/
- API文档: http://localhost:8000/api/docs
- ReDoc文档: http://localhost:8000/api/redoc


### 19.5 代码规范检查

#### Ruff 代码检查

```bash
# 检查代码
ruff check .

# 自动修复问题
ruff check . --fix

# 代码格式化
ruff format .
```

#### MyPy 类型检查

```bash
# 运行类型检查
mypy src/

# MyPy 配置在宽松模式下运行
# 138个类型错误是Django ORM的已知限制，不影响项目运行
```

#### 一键检查脚本

```bash
# 运行所有检查
bash scripts/lint.sh
```

### 19.6 单元测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_models/test_user_models.py

# 运行特定测试
pytest tests/test_models/test_user_models.py::TestUserModel::test_create_user

# 显示详细输出
pytest -v

# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 仅运行单元测试
pytest -m unit

# 仅运行集成测试
pytest -m integration
```

测试配置：
- 使用 `pytest` + `pytest-django` 测试框架
- 配置文件：`pyproject.toml`
- 测试路径：`tests/`
- 期望覆盖率：> 80%

### 19.7 服务部署

#### Docker 部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 生产环境部署

1. **环境变量配置**

创建 `.env` 文件：
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://host:port/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

2. **数据库迁移**



4. **使用 Gunicorn + Nginx 部署**

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

5. **使用 Supervisor 管理进程**

```ini
[program:django-ninja-api]
directory=/path/to/FastApi
command=/path/to/.venv/bin/gunicorn config.wsgi:application --workers 4 --bind 0.0.0.0:8000
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/django-ninja-api.log
```

### 19.8 数据库管理



### 19.9 常用命令

```bash
# 创建超级用户
python manage.py createsuperuser

# Django 管理命令
python manage.py shell
python manage.py dbshell

# 清除缓存（如使用Redis）
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

---

## 20. 开发工作流

### 20.1 代码提交前检查

```bash
# 1. 运行代码检查
ruff check . --fix
ruff format .

# 2. 运行类型检查
mypy src/

# 3. 运行测试
pytest

# 4. 提交代码
git add .
git commit -m "feat: your message"
```

### 20.2 分支策略

- `main`: 生产环境分支
- `develop`: 开发主分支
- `feature/*`: 功能开发分支
- `bugfix/*`: 缺陷修复分支
- `hotfix/*`: 紧急修复分支

### 20.3 代码质量标准

- **代码风格**: 符合 PEP 8 规范
- **类型提示**: 所有公共接口使用类型提示
- **文档字符串**: 使用 Google 风格 docstring
- **测试覆盖**: 核心业务逻辑覆盖率 ≥ 80%
- **代码检查**: 通过 Ruff 检查（0 错误）
- **类型检查**: MyPy 类型检查通过（宽松模式）

---

## 21. 故障排查

### 21.1 常见问题



## 13. 后续扩展

- 事件驱动机制（Domain Events）
- 微服务架构
- OAuth 2.0 认证
- API 网关统一鉴权
- Kubernetes 编排部署
- DevOps 自动化流水线

---

## 14. 总结


