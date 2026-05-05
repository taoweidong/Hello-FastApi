# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 项目概述

基于 FastAPI 的 RESTful API 服务，采用 DDD（领域驱动设计）四层架构，实现 JWT 双令牌认证和 RBAC 权限控制。项目使用 FastCRUD 库简化仓储层 CRUD 操作，全面支持异步处理。

## 常用命令

### 开发环境设置
```bash
# 安装 UV 包管理器
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv --python 3.10
source .venv/bin/activate  # Linux/Mac
uv pip install -e ".[dev]"
```

### 数据库初始化（按顺序执行）
```bash
python -m scripts.cli initdb          # 创建数据库表
python -m scripts.cli seedrbac        # 初始化角色和权限
python -m scripts.cli seeddata        # 初始化测试数据
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
```

### 开发服务
```bash
python -m scripts.cli runserver       # 启动开发服务器（端口 8000）
# API 文档: http://localhost:8000/api/docs
```

### 测试
```bash
pytest                                # 运行所有测试
pytest tests/unit/                    # 运行单元测试
pytest tests/integration/             # 运行集成测试
pytest -v --tb=short                  # 详细输出
pytest --cov=src --cov-report=term-missing  # 带覆盖率报告
```

### 代码质量
```bash
ruff check . --fix                    # Ruff 代码检查并自动修复
ruff format .                         # Ruff 代码格式化
mypy src/                             # MyPy 类型检查
mypy src/ --strict --config-file=mypy.ini  # 严格类型检查
```

### 环境切换
```bash
export APP_ENV=production             # Linux/Mac
set APP_ENV=production                # Windows
```

## 架构设计

### DDD 四层架构

项目采用严格的四层架构设计，遵循依赖倒置原则（DIP）：

**1. API 层 (`src/api/`)**
- 职责：HTTP 请求处理、认证授权、响应格式化
- 文件：`v1/*_routes.py` 定义路由端点，`dependencies.py` 提供依赖注入
- 关键点：
  - 所有路由通过 `dependencies.py` 中的工厂函数注入服务
  - 使用 `@field_validator` 进行请求参数验证
  - 统一响应格式通过 `api/common.py` 中的工具函数处理

**2. 应用层 (`src/application/`)**
- 职责：用例编排、业务流程协调、DTO 定义
- 目录：`services/` 应用服务，`dto/` 数据传输对象
- 关键点：
  - 应用服务协调多个仓储完成复杂业务逻辑
  - DTO 用于接口层数据验证和转换
  - 事务控制在应用服务层管理（通过 AsyncSession）

**3. 领域层 (`src/domain/`)**
- 职责：核心业务逻辑、领域实体、仓储接口定义
- 目录：`entities/` 领域实体，`repositories/` 仓储接口，`services/` 领域服务
- 关键点：
  - 仓储接口定义在 `domain/repositories/`，实现在 `infrastructure/repositories/`
  - 领域服务（如 PasswordService、TokenService）封装通用业务逻辑
  - 使用 `TYPE_CHECKING` 避免循环导入，返回类型为字符串形式的模型类

**4. 基础设施层 (`src/infrastructure/`)**
- 职责：技术实现、数据库操作、外部服务集成
- 目录：`database/` 数据库配置和模型，`repositories/` 仓储实现，`cache/` 缓存实现
- 关键点：
  - 所有仓储实现使用 FastCRUD 简化基础 CRUD 操作
  - 仓储方法签名必须与领域层接口定义一致
  - 数据库模型定义在 `infrastructure/database/models.py`

### 核心架构模式

**依赖注入模式**
- 所有服务通过 `api/dependencies.py` 中的工厂函数创建
- 路由层使用 `Depends()` 注入服务和认证依赖
- 认证流程：`get_current_user_id` → `get_current_active_user` → `require_permission`

**仓储模式**
- 接口定义在 `domain/repositories/`，使用 ABC 抽象基类
- 实现在 `infrastructure/repositories/`，继承接口并使用 FastCRUD
- 类型注解：返回类型为具体模型类（如 `User | None`），使用 `TYPE_CHECKING` 避免循环导入

**FastCRUD 集成**
- 仓储实现使用 `FastCRUD[ModelType]` 封装基础 CRUD
- 复杂查询保留自定义实现（如时间范围查询、多表关联）
- 示例：`self.crud = FastCRUD(User)`

**JWT 双令牌认证**
- Access Token：短期令牌（默认 30 分钟），用于 API 访问
- Refresh Token：长期令牌（默认 7 天），用于刷新 Access Token
- 令牌服务：`domain/services/token_service.py`，注入到 `AuthService`

**RBAC 权限模型**
- 用户 → 角色 → 权限 三层模型
- 权限检查：通过 `require_permission(code)` 依赖工厂验证权限码
- 超级用户：`is_superuser=True` 自动拥有所有权限

### 数据库设计规范

**表命名规范**
- 所有表名前缀：`sys_`（如 `sys_users`, `sys_roles`）
- 关联表：`sys_role_permissions`（角色-权限关联）

**主键设计**
- 主键字段：`id`，类型为 `str`
- 值格式：36 位 UUID 字符串（使用 `uuid.uuid4()` 生成）

**时间字段**
- `created_at`：创建时间，自动设置
- `updated_at`：更新时间，自动更新

### 异步架构

**全面异步支持**
- 所有数据库操作使用异步方法（`async def`）
- 仓储方法：`async def get_by_id(...) -> User | None`
- 应用服务：`async def create_user(...) -> UserResponseDTO`
- 使用 `AsyncSession` 进行数据库会话管理

**异步上下文管理**
- 数据库会话通过 `get_db()` 依赖注入
- 生命周期管理在 `main.py` 的 `lifespan()` 函数中

### 类型系统

**类型注解规范**
- 所有公共接口必须有类型注解
- 使用 Python 3.10+ 联合类型语法：`str | None` 而非 `Optional[str]`
- 泛型使用：`Generic[T]` 继承，如 `class UnifiedResponse(BaseModel, Generic[T])`
- 避免 `Any` 类型，使用具体类型或泛型

**类型检查配置**
- 配置文件：`mypy.ini`
- 严格模式：`strict = True`
- 第三方库忽略：SQLModel、FastAPI、Pydantic 等

### 配置管理

**多环境配置**
- 配置文件：`.env.development`, `.env.production`, `.env.testing`
- 环境变量：`APP_ENV` 切换环境
- 加载优先级：系统环境变量 > `.env.{APP_ENV}` > `.env` > 默认值

**配置类**
- 配置定义：`config/settings.py`，继承 `BaseSettings`
- 使用 Pydantic 自动验证和类型转换

### 错误处理

**自定义异常**
- 异常定义：`core/exceptions.py`
- 常见异常：`NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`
- 全局异常处理在 `main.py` 中注册

**响应格式**
- 成功响应：`{"code": 0, "message": "操作成功", "data": {...}}`
- 错误响应：`{"code": 400, "message": "错误描述"}`

## 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用 Ruff 进行代码格式化和检查
- 所有代码注释使用中文描述
- 行长度限制：320 字符（`pyproject.toml` 配置）

### 仓储开发模式

**创建新仓储的步骤：**
1. 在 `infrastructure/database/models.py` 定义 SQLModel 模型
2. 在 `domain/repositories/` 定义抽象接口（ABC）
3. 在 `infrastructure/repositories/` 实现接口，使用 FastCRUD
4. 在 `api/dependencies.py` 添加仓储工厂函数
5. 在 `application/services/` 创建应用服务，注入仓储
6. 在 `api/v1/` 创建路由，注入服务

**仓储方法命名规范：**
- `get_by_id(id)` - 根据 ID 获取单个实体
- `get_all(skip, limit)` - 分页获取列表
- `create(entity)` - 创建实体
- `update(entity)` - 更新实体
- `delete(id)` - 删除实体
- `count()` - 统计总数

### DTO 开发模式

**DTO 类结构：**
- `CreateDTO` - 创建请求
- `UpdateDTO` - 更新请求
- `ResponseDTO` - 响应数据
- `QueryDTO` - 查询参数

**验证器使用：**
- 使用 `@field_validator` 进行字段验证
- 公共验证器：`core/validators.py`（如 `empty_str_to_none`, `normalize_optional_id`）
- 前端数据清洗：空字符串转 None，字符串 ID 转整型等

### 测试策略

**测试目录结构：**
- `tests/unit/` - 单元测试（测试应用服务和领域逻辑）
- `tests/integration/` - 集成测试（测试 API 端点）

**测试标记：**
- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试

**异步测试：**
- pytest-asyncio 自动模式（`asyncio_mode = "auto"`）
- 测试函数使用 `async def`，数据库会话通过 fixture 注入

## 关键技术点

### FastCRUD 使用

FastCRUD 封装了常见 CRUD 操作，减少重复代码：

```python
from fastcrud import FastCRUD

class UserRepository:
    def __init__(self, session: AsyncSession):
        self.crud = FastCRUD(User)
    
    async def get_by_id(self, user_id: str) -> User | None:
        return await self.crud.get_one(session, id=user_id)
    
    async def create(self, user: User) -> User:
        return await self.crud.create(session, user)
```

### JWT 认证流程

1. 登录：`AuthService.login()` 验证密码，生成双令牌
2. 访问：请求头携带 `Authorization: Bearer <access_token>`
3. 验证：`get_current_user_id` 解码令牌，提取用户 ID
4. 刷新：`AuthService.refresh_token()` 使用 Refresh Token 刷新 Access Token

### RBAC 权限检查

权限检查通过依赖注入实现：

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_permission("user:delete")),
    user_service: UserService = Depends(get_user_service)
):
    # 只有拥有 "user:delete" 权限的用户才能访问
    ...
```

## 注意事项

- **事务管理**：应用服务层负责事务边界，通过 `AsyncSession` 管理
- **循环导入**：使用 `TYPE_CHECKING` 和字符串形式的类型注解避免
- **异步一致性**：所有数据库操作保持异步，避免混合同步代码
- **错误处理**：使用自定义异常，避免直接抛出通用异常
- **类型安全**：通过 mypy 严格模式检查，避免运行时类型错误
- **代码注释**：所有注释使用中文，保持与代码逻辑一致
