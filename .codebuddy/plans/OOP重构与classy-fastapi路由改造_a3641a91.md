---
name: OOP重构与classy-fastapi路由改造
overview: 将FastAPI项目从函数式路由重构为面向对象设计：1)引入classy-fastapi将6个路由模块改为类设计；2)将DI工厂、数据库连接、缓存、异常处理等模块改为面向对象；3)适配所有单元测试和集成测试确保通过；4)遵循FastAPI最佳实践。
todos:
  - id: infra-database
    content: 重构 DatabaseManager 类，封装 engine/session/lifecycle，保持 get_db 工厂函数兼容
    status: completed
  - id: infra-redis-exception-logging
    content: 重构 RedisManager、ExceptionHandlerRegistry、LoggingManager 为类设计
    status: completed
  - id: di-refactor
    content: 重构 dependencies.py，按领域分组组织 DI 工厂，保持 Depends 兼容
    status: completed
    dependencies:
      - infra-database
  - id: route-auth-user
    content: 重构 AuthRouter 和 UserRouter 为 classy-fastapi 类，使用 [skill:python-code-quality] 审查
    status: completed
    dependencies:
      - di-refactor
  - id: route-role-perm-menu
    content: 重构 RoleRouter、PermissionRouter、MenuRouter 为 classy-fastapi 类
    status: completed
    dependencies:
      - di-refactor
  - id: route-system-split
    content: 拆分 system_routes.py 为 DeptRouter、LogRouter、MonitorRouter 三个类
    status: completed
    dependencies:
      - di-refactor
  - id: route-aggregate-main
    content: 更新 v1/__init__.py 路由聚合和 main.py 注册方式，删除旧路由文件
    status: completed
    dependencies:
      - route-auth-user
      - route-role-perm-menu
      - route-system-split
  - id: test-adapt
    content: 适配所有测试文件的导入路径和注册方式，确保全部通过
    status: completed
    dependencies:
      - route-aggregate-main
---

## 产品概述

对现有 FastAPI + DDD + RBAC 后端项目进行结构优化和路由重构，提升代码的面向对象程度和可维护性。**严格遵循"一个 py 文件只定义一个类"原则**，所有多类文件必须拆分。

## 核心功能

- **路由层重构**：将6个函数式路由文件重构为 classy-fastapi 类设计，每个路由文件对应一个 Router 类
- **基础设施层面向对象化**：将数据库连接、Redis缓存、异常处理注册、日志配置等从函数式/模块级变量重构为类管理模式
- **多类文件拆分**：将 models.py（12个类）、common.py（5个类）、middlewares.py（2个类）等按"一文件一类"拆分
- **DI层按领域拆分**：将 dependencies.py 按领域分组为独立文件
- **单元测试适配**：所有测试用例适配新的导入路径，功能不变，全部通过
- **FastAPI 最佳实践**：参考官方教程，确保依赖注入、路由注册、中间件等采用最优实践

## 技术栈

- **框架**: FastAPI + classy-fastapi (>=0.7.0，已在 pyproject.toml 中)
- **ORM**: SQLModel + FastCRUD
- **数据库**: SQLite (开发/测试) / PostgreSQL/MySQL (生产)
- **测试**: pytest + pytest-asyncio + httpx
- **包管理**: uv (uv.lock)

## 实现方案

### 核心原则

**一个 py 文件只定义一个类**——所有多类文件必须拆分，每个类独占一个文件，通过 `__init__.py` 统一导出。纯工具函数文件（无类定义）可保留函数式。

### 核心策略

1. **路由层**：每个路由文件重构为继承 `Routable` 的类，端点方法用 `@route` 装饰器，服务通过构造函数 `Depends` 注入
2. **基础设施层**：将函数式模块重构为 Manager 类，通过 `get_*` 工厂函数暴露单例，保持与 FastAPI `Depends` 兼容
3. **多类拆分**：models.py → models/ 目录、common.py → common/ 目录、middlewares.py → 拆分两个文件
4. **DI层**：按领域拆分为 dependencies/ 目录，每个文件包含一组相关工厂函数
5. **测试适配**：更新导入路径和路由注册方式，测试逻辑不变

### 关键技术决策

- **classy-fastapi 路由注册**：实例化 Router 类后，通过 `router.router` 获取 `APIRouter` 注册到应用
- **依赖注入策略**：Router 类构造函数接收服务依赖 `Depends(get_xxx_service)`，保持 DI 工厂函数兼容
- **system_routes.py 拆分**：拆为 `DeptRouter`、`LogRouter`、`MonitorRouter` 三个类
- **models.py 拆分**：12个ORM模型类拆为 models/ 目录，每个类一个文件，`__init__.py` 统一导出
- **入口函数保留函数式**：`create_app()`、`get_db()`、lifespan 等保持函数式
- **工具函数保留函数式**：`validators.py`、`utils.py` 等纯函数文件保留

### 实施注意事项

- **路由路径一致性**：重构后所有 API 路径、请求方法、响应格式必须与现有完全一致
- **导入兼容**：拆分后的 `__init__.py` 必须保持原有公共导入路径可用（如 `from src.infrastructure.database.models import User`）
- **classy-fastapi @route**：`@route.post("")` 对应根路径，与原 `@router.post("")` 行为一致
- **测试导入路径**：集成测试 HTTP 路径不变，但 Python 导入路径需适配

## 架构设计

### 重构后完整目录结构

```
service/src/
├── main.py                              # 应用工厂（保留函数式）
├── api/
│   ├── common/                          # [NEW] 拆分为包
│   │   ├── __init__.py                  # 统一导出
│   │   ├── response_models.py           # UnifiedResponse 类
│   │   ├── page_response.py             # PageResponse 类
│   │   ├── error_response.py            # ErrorResponse 类
│   │   ├── message_response.py          # MessageResponse 类
│   │   ├── health_response.py           # HealthResponse 类
│   │   ├── response_builder.py          # success_response/list_response/page_response/error_response 函数
│   │   ├── user_formatter.py            # format_user_list_row 函数
│   │   └── model_utils.py               # model_to_dict/models_to_list/datetime_to_* 函数
│   ├── constants.py                     # 常量（保留）
│   ├── dependencies/                    # [NEW] 拆分为包
│   │   ├── __init__.py                  # 统一导出所有工厂函数
│   │   ├── auth.py                      # 认证依赖：get_current_user_id, get_current_active_user, require_permission, require_superuser
│   │   ├── domain_services.py           # 领域服务工厂：get_password_service, get_token_service
│   │   ├── auth_service.py              # get_auth_service
│   │   ├── user_service.py              # get_user_service, get_user_repository
│   │   ├── role_service.py              # get_role_service, get_role_repository
│   │   ├── permission_service.py        # get_permission_service
│   │   ├── menu_service.py              # get_menu_service, get_menu_repository
│   │   ├── department_service.py        # get_department_service
│   │   └── log_service.py               # get_log_service
│   └── v1/
│       ├── __init__.py                  # 路由聚合
│       ├── auth_router.py               # [MODIFY] AuthRouter 类
│       ├── user_router.py               # [MODIFY] UserRouter 类
│       ├── role_router.py               # [MODIFY] RoleRouter 类
│       ├── permission_router.py         # [MODIFY] PermissionRouter 类
│       ├── menu_router.py               # [MODIFY] MenuRouter 类
│       ├── dept_router.py               # [NEW] DeptRouter 类
│       ├── log_router.py                # [NEW] LogRouter 类
│       └── monitor_router.py            # [NEW] MonitorRouter 类
├── application/                         # 应用层（已面向对象 ✅）
│   ├── validators.py                    # 保留函数式（纯工具函数）
│   ├── dto/                             # ✅ 每个文件一个DTO类
│   └── services/                        # ✅ 每个文件一个Service类
├── config/                              # ✅ 已面向对象
├── domain/                              # ✅ 已面向对象（每文件一个类）
└── infrastructure/
    ├── cache/
    │   ├── __init__.py                  # 更新导出
    │   └── redis_manager.py             # [MODIFY→RENAME] RedisManager 类
    ├── common/
    │   ├── __init__.py                  # 更新导出
    │   └── utils.py                     # 保留函数式（纯工具函数）
    ├── database/
    │   ├── __init__.py                  # 更新导出
    │   ├── database_manager.py          # [NEW] DatabaseManager 类
    │   └── models/                      # [NEW] 拆分为包
    │       ├── __init__.py              # 统一导出所有模型类
    │       ├── user.py                  # User 类
    │       ├── user_role.py             # UserRole 类
    │       ├── role.py                  # Role 类
    │       ├── permission.py            # Permission 类
    │       ├── role_permission_link.py  # RolePermissionLink 类
    │       ├── menu.py                  # Menu 类
    │       ├── role_menu_link.py        # RoleMenuLink 类
    │       ├── department.py            # Department 类
    │       ├── login_log.py             # LoginLog 类
    │       ├── operation_log.py         # OperationLog 类
    │       ├── system_log.py            # SystemLog 类
    │       └── ip_rule.py              # IPRule 类
    ├── http/
    │   ├── __init__.py                  # 更新导出
    │   ├── exception_handler_registry.py # [NEW] ExceptionHandlerRegistry 类
    │   ├── request_logging_middleware.py  # [NEW] RequestLoggingMiddleware 类
    │   └── ip_filter_middleware.py       # [NEW] IPFilterMiddleware 类
    ├── lifecycle/
    │   ├── __init__.py                  # 更新导出
    │   └── lifespan.py                  # 保留函数式（上下文管理器）
    ├── logging/
    │   ├── __init__.py                  # 更新导出
    │   ├── logging_manager.py           # [NEW] LoggingManager 类
    │   └── decorators.py                # 保留函数式（装饰器）
    └── repositories/                    # ✅ 每个文件一个Repository类
```

## 目录结构（变更明细）

### 路由层变更

```
service/src/api/v1/
├── auth_router.py          # [MODIFY] AuthRouter(Routable) 类，12端点
├── user_router.py          # [MODIFY] UserRouter(Routable) 类，11端点
├── role_router.py          # [MODIFY] RoleRouter(Routable) 类，8端点
├── permission_router.py    # [MODIFY] PermissionRouter(Routable) 类，3端点
├── menu_router.py          # [MODIFY] MenuRouter(Routable) 类，6端点
├── dept_router.py          # [NEW] DeptRouter(Routable) 类，4端点
├── log_router.py           # [NEW] LogRouter(Routable) 类，9端点
├── monitor_router.py       # [NEW] MonitorRouter(Routable) 类，5端点
├── __init__.py             # [MODIFY] 适配新Router类注册方式
├── auth_routes.py          # [DELETE]
├── user_routes.py          # [DELETE]
├── role_routes.py          # [DELETE]
├── permission_routes.py    # [DELETE]
├── menu_routes.py          # [DELETE]
└── system_routes.py        # [DELETE]
```

### 数据库模型层变更（models.py → models/ 包）

```
service/src/infrastructure/database/
├── database_manager.py     # [NEW] DatabaseManager 类
├── models/                 # [NEW] 包替代原 models.py
│   ├── __init__.py         # 统一导出所有12个模型类
│   ├── user.py             # User 类
│   ├── user_role.py        # UserRole 类
│   ├── role.py             # Role 类
│   ├── permission.py       # Permission 类
│   ├── role_permission_link.py # RolePermissionLink 类
│   ├── menu.py             # Menu 类
│   ├── role_menu_link.py   # RoleMenuLink 类
│   ├── department.py       # Department 类
│   ├── login_log.py        # LoginLog 类
│   ├── operation_log.py    # OperationLog 类
│   ├── system_log.py       # SystemLog 类
│   └── ip_rule.py          # IPRule 类
├── models.py               # [DELETE] 已拆分为 models/ 包
└── connection.py           # [DELETE] 已重构为 database_manager.py
```

### API公共层变更（common.py → common/ 包）

```
service/src/api/common/
├── __init__.py              # 统一导出所有公共组件
├── unified_response.py      # UnifiedResponse 类
├── page_response.py         # PageResponse 类
├── error_response.py        # ErrorResponse 类
├── message_response.py      # MessageResponse 类
├── health_response.py       # HealthResponse 类
├── response_builder.py      # success_response/list_response/page_response/error_response 函数
├── user_formatter.py        # format_user_list_row 函数
└── model_utils.py           # model_to_dict/models_to_list/datetime_to_*/safe_str/safe_int 函数
└── common.py                # [DELETE] 已拆分为 common/ 包
```

### DI层变更（dependencies.py → dependencies/ 包）

```
service/src/api/dependencies/
├── __init__.py              # 统一导出所有工厂函数
├── auth.py                  # get_current_user_id, get_current_active_user, require_permission, require_superuser
├── domain_services.py       # get_password_service, get_token_service
├── auth_service.py          # get_auth_service
├── user_service.py          # get_user_service, get_user_repository
├── role_service.py          # get_role_service, get_role_repository
├── permission_service.py    # get_permission_service
├── menu_service.py          # get_menu_service, get_menu_repository
├── department_service.py    # get_department_service
└── log_service.py           # get_log_service
└── dependencies.py          # [DELETE] 已拆分为 dependencies/ 包
```

### 中间件层变更（middlewares.py → 拆分为两个文件）

```
service/src/infrastructure/http/
├── __init__.py                  # 更新导出
├── exception_handler_registry.py # [NEW] ExceptionHandlerRegistry 类
├── request_logging_middleware.py # [NEW] RequestLoggingMiddleware 类
├── ip_filter_middleware.py      # [NEW] IPFilterMiddleware 类
├── exception_handlers.py       # [DELETE] 已重构为 exception_handler_registry.py
└── middlewares.py               # [DELETE] 已拆分为两个文件
```

### 基础设施其他变更

```
service/src/infrastructure/
├── cache/
│   ├── redis_manager.py         # [NEW] RedisManager 类
│   └── redis_client.py         # [DELETE] 已重构为 redis_manager.py
├── logging/
│   ├── logging_manager.py      # [NEW] LoggingManager 类
│   └── logger.py               # [DELETE] 已重构为 logging_manager.py
```

### 测试文件变更

```
service/tests/
├── conftest.py                         # [MODIFY] 适配新导入路径
├── integration/
│   ├── conftest.py                     # [MODIFY] 适配新导入路径
│   ├── test_api.py                     # [MODIFY] 适配新导入路径
│   ├── test_api_real_flow.py           # [MODIFY] 适配新导入路径
│   └── db_seed.py                      # [MODIFY] 适配 models 包导入
└── unit/
    ├── test_auth.py                    # 保留不变
    ├── test_core.py                    # [MODIFY] 适配 utils 导入路径
    ├── test_dto_validators.py          # 保留不变
    ├── test_user_service.py            # [MODIFY] 适配 models 包导入
    └── test_validators.py              # 保留不变
```

## 关键代码结构

### classy-fastapi Router 类示例（UserRouter）

```python
# user_router.py — 一个文件只定义 UserRouter 一个类
from classy_fastapi import Routable, route
from fastapi import Depends
from src.api.common import success_response, list_response, format_user_list_row
from src.api.dependencies import get_user_service, get_current_user_id, require_permission
from src.application.dto.user_dto import UserCreateDTO, UserListQueryDTO, UserUpdateDTO, ...
from src.application.services.user_service import UserService

class UserRouter(Routable):
    def __init__(
        self,
        user_service: UserService = Depends(get_user_service),
    ):
        super().__init__()
        self.user_service = user_service

    @route.post("")
    async def get_user_list(
        self,
        query: UserListQueryDTO,
        _: dict = Depends(require_permission("user:view")),
    ):
        users, total = await self.user_service.get_users(query)
        user_list = [format_user_list_row(user.model_dump()) for user in users]
        return list_response(list_data=user_list, total=total, ...)

    @route.post("/create", status_code=201)
    async def create_user(self, dto: UserCreateDTO, _: dict = Depends(require_permission("user:add"))):
        user = await self.user_service.create_user(dto)
        return success_response(data=user, message="创建成功", code=201)
    # ... 其余端点
```

### DatabaseManager 类示例

```python
# database_manager.py — 一个文件只定义 DatabaseManager 一个类
class DatabaseManager:
    def __init__(self, database_url: str, echo: bool = False):
        self._engine = create_async_engine(database_url, echo=echo, pool_pre_ping=True)

    @property
    def engine(self): return self._engine

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSession(self._engine, expire_on_commit=False) as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def init_tables(self) -> None: ...
    async def dispose(self) -> None: ...
```

### models/**init**.py 统一导出

```python
# models/__init__.py — 统一导出保持向后兼容
from src.infrastructure.database.models.user import User
from src.infrastructure.database.models.user_role import UserRole
from src.infrastructure.database.models.role import Role
from src.infrastructure.database.models.permission import Permission
from src.infrastructure.database.models.role_permission_link import RolePermissionLink
from src.infrastructure.database.models.menu import Menu
from src.infrastructure.database.models.role_menu_link import RoleMenuLink
from src.infrastructure.database.models.department import Department
from src.infrastructure.database.models.login_log import LoginLog
from src.infrastructure.database.models.operation_log import OperationLog
from src.infrastructure.database.models.system_log import SystemLog
from src.infrastructure.database.models.ip_rule import IPRule

__all__ = [
    "User", "UserRole", "Role", "Permission", "RolePermissionLink",
    "Menu", "RoleMenuLink", "Department",
    "LoginLog", "OperationLog", "SystemLog", "IPRule",
]
```

### 路由聚合（v1/**init**.py）

```python
from fastapi import APIRouter
from src.api.v1.auth_router import AuthRouter
from src.api.v1.user_router import UserRouter
from src.api.v1.role_router import RoleRouter
from src.api.v1.permission_router import PermissionRouter
from src.api.v1.menu_router import MenuRouter
from src.api.v1.dept_router import DeptRouter
from src.api.v1.log_router import LogRouter
from src.api.v1.monitor_router import MonitorRouter

system_router = APIRouter()
system_router.include_router(AuthRouter().router, tags=["认证管理"])
system_router.include_router(UserRouter().router, prefix="/user", tags=["用户管理"])
system_router.include_router(RoleRouter().router, prefix="/role", tags=["角色管理"])
system_router.include_router(PermissionRouter().router, prefix="/permission", tags=["权限管理"])
system_router.include_router(MenuRouter().router, prefix="/menu", tags=["菜单管理"])
system_router.include_router(DeptRouter().router, tags=["部门管理"])
system_router.include_router(LogRouter().router, tags=["日志管理"])
system_router.include_router(MonitorRouter().router, tags=["系统监控"])

__all__ = ["system_router"]
```

## Skill

- **python-code-quality**: 确保重构后的代码遵循面向对象最佳实践，SOLID原则，类型注解完整性，Python 3.10+现代特性使用

## SubAgent

- **code-explorer**: 在实现阶段搜索跨文件依赖和引用关系，确保重构不遗漏任何调用点