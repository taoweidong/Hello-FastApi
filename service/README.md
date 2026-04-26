# Hello-FastApi 后端服务

基于 FastAPI 框架的 RESTful API 服务，采用 DDD（领域驱动设计）架构，支持 JWT 双令牌认证和 RBAC 权限控制。

## 核心特性

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
│   ├── api/                    # API 文档
│   ├── design/                 # 架构设计文档
│   └── guide/                  # 使用指南
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

### 安装

```bash
cd service

# 创建虚拟环境
uv venv --python 3.10

# 激活虚拟环境
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 数据库初始化

```bash
# 1. 创建数据库表
python -m scripts.cli initdb

# 2. 初始化测试数据（菜单、日志等）
python -m scripts.cli seeddata

# 3. 初始化 RBAC 数据（角色、菜单权限分配）
python -m scripts.cli seedrbac

# 4. 创建超级管理员（自动分配 admin 角色，拥有所有菜单权限）
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
```

### 启动服务

```bash
python -m scripts.cli runserver
```

服务启动后访问：
- API 文档: http://localhost:8000/api/docs
- ReDoc 文档: http://localhost:8000/api/redoc

## 单元测试

```bash
pytest                                    # 运行所有测试（1850 tests）
pytest tests/unit/                        # 仅单元测试
pytest --cov=src --cov-report=term-missing # 带覆盖率
```

## 规范检查

```bash
ruff check . --fix    # Lint + 自动修复
ruff format .         # 格式化
mypy src/             # 类型检查
```

## 📖 文档导航

| 文档 | 说明 |
|------|------|
| [管理命令](docs/guide/cli-commands.md) | CLI 命令详细说明（initdb、seedrbac、createsuperuser 等） |
| [环境配置](docs/guide/environment.md) | 多环境切换、配置项说明、.env 文件详解 |
| [开发规范](docs/guide/development.md) | 代码风格、数据库规范、DDD 分层约束、API 响应格式 |
| [部署](docs/guide/deployment.md) | Docker 部署、生产环境部署、Nginx 反向代理 |
| [测试](docs/guide/testing.md) | 测试策略、编写测试、覆盖率配置 |
| [架构设计](docs/design/项目架构设计与约束.md) | DDD 分层架构、依赖约束、代码示例 |

## 📊 代码质量报告

| 报告 | 说明 |
|------|------|
| [代码质量分析报告](docs/code-quality-report.md) | Ruff/MyPy/Pytest 检查结果、架构分析、改进建议 |
| [系统框架分析报告](docs/design/系统框架分析报告.md) | 架构分层分析、问题清单、改进计划 |
| [大型项目演进路线图](docs/design/大型项目演进路线图.md) | 分阶段改进计划 |

## 许可证

MIT License
