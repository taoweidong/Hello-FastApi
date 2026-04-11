# Service项目全面重构优化计划

## 重构目标

1. 统一采用面向对象开发模式，消除函数式编程（除入口函数外）
2. 文件按功能合理拆分，符合DDD架构和FastAPI最佳实践
3. 完善单元测试，测试覆盖率提升至80%+
4. 所有测试用例100%通过

## 重构任务

### Task 1: 统一仓储层依赖注入模式

**问题**: MenuRepository、DepartmentRepository、LogRepository 未在构造函数接收 session，与其他仓储不一致

**修改文件**:
- `src/infrastructure/repositories/menu_repository.py` - 已在构造函数添加 session，需更新所有方法签名
- `src/infrastructure/repositories/department_repository.py` - 已在构造函数添加 session，需更新所有方法签名  
- `src/infrastructure/repositories/log_repository.py` - 已在构造函数添加 session，需更新所有方法签名

**修改内容**:
```python
# 修改前
async def get_all(self, session: AsyncSession) -> list[Menu]:
    result = await self._crud.get_multi(session, ...)

# 修改后  
async def get_all(self) -> list[Menu]:
    result = await self._crud.get_multi(self.session, ...)
```

**调用方更新**:
- `src/application/services/menu_service.py` - 移除所有方法中的 session 参数传递
- `src/application/services/department_service.py` - 移除所有方法中的 session 参数传递
- `src/application/services/log_service.py` - 移除所有方法中的 session 参数传递
- `src/api/v1/auth_routes.py#L214` - `menu_repo.get_all(db)` 改为 `menu_repo.get_all()`

**预估修改**: 约30处调用点

---

### Task 2: 路由层采用 classy-fastapi 简化控制器设计

**参考**: https://pypi.org/project/classy-fastapi/

**当前问题**: 
- 路由使用函数式定义，缺乏封装
- 依赖注入需要全局变量或复杂的 Depends 机制
- 手动注册路由繁琐，代码重复

**引入 classy-fastapi 库**:
```bash
# 添加到 pyproject.toml
dependencies = [
    "classy-fastapi>=0.7.0",
]
```

**控制器设计示例**:
```python
# src/api/v1/user_routes.py
from classy_fastapi import Routable, get, post, put, delete
from src.api.dependencies import get_user_service, require_permission
from src.api.common import format_user_list_row, list_response, success_response

class UserController(Routable):
    """用户管理控制器 - 基于类的路由"""
    
    def __init__(
        self,
        prefix: str = "/user",
        tags: list[str] = ["用户管理"]
    ):
        """初始化控制器
        
        Args:
            prefix: 路由前缀
            tags: OpenAPI 标签
        """
        super().__init__(prefix=prefix, tags=tags)
    
    @post("", dependencies=[Depends(require_permission("user:view"))])
    async def get_user_list(
        self,
        query: UserListQueryDTO,
        service: UserService = Depends(get_user_service)
    ):
        """获取用户列表（支持筛选和分页）
        
        Args:
            query: 用户列表查询参数
            service: 用户服务实例（通过 DI 注入）
            
        Returns:
            Pure Admin 标准分页响应格式的用户列表
        """
        users, total = await service.get_users(query)
        user_list = [format_user_list_row(user.model_dump()) for user in users]
        return list_response(list_data=user_list, total=total, page_size=query.pageSize, current_page=query.pageNum)
    
    @post("/create", status_code=201, dependencies=[Depends(require_permission("user:add"))])
    async def create_user(
        self,
        dto: UserCreateDTO,
        service: UserService = Depends(get_user_service)
    ):
        """创建用户
        
        Args:
            dto: 用户创建数据
            service: 用户服务实例（通过 DI 注入）
            
        Returns:
            统一格式的成功响应，包含创建的用户信息
        """
        user = await service.create_user(dto)
        return success_response(data=user, message="创建成功", code=201)
    
    @get("/info")
    async def get_current_user_info(
        self,
        user_id: str = Depends(get_current_user_id),
        service: UserService = Depends(get_user_service)
    ):
        """获取当前登录用户信息
        
        Args:
            user_id: 当前用户ID
            service: 用户服务实例（通过 DI 注入）
            
        Returns:
            统一格式的成功响应，包含当前用户完整信息（含角色权限）
        """
        user = await service.get_user(user_id)
        return success_response(data=user)
    
    @get("/{user_id}", dependencies=[Depends(require_permission("user:view"))])
    async def get_user_detail(
        self,
        user_id: str,
        service: UserService = Depends(get_user_service)
    ):
        """获取用户详情"""
        user = await service.get_user(user_id)
        return success_response(data=user)
    
    @put("/{user_id}", dependencies=[Depends(require_permission("user:edit"))])
    async def update_user(
        self,
        user_id: str,
        dto: UserUpdateDTO,
        service: UserService = Depends(get_user_service)
    ):
        """更新用户"""
        user = await service.update_user(user_id, dto)
        return success_response(data=user, message="更新成功")
    
    @delete("/{user_id}", dependencies=[Depends(require_permission("user:delete"))])
    async def delete_user(
        self,
        user_id: str,
        service: UserService = Depends(get_user_service)
    ):
        """删除用户"""
        await service.delete_user(user_id)
        return success_response(message="删除成功")
```

**依赖注入优势 - 无需全局变量**:
```python
# src/api/v1/__init__.py
from src.api.v1.user_routes import UserController
from src.api.v1.auth_routes import AuthController
from src.infrastructure.repositories.user_repository import UserRepository
from src.domain.services.password_service import PasswordService

def create_system_router():
    """创建系统路由并注入依赖"""
    system_router = APIRouter(prefix="/api/system")
    
    # 示例：注入依赖到控制器
    # 可以在这里传入任何依赖，无需全局变量
    user_controller = UserController()
    auth_controller = AuthController()
    
    # 自动注册所有控制器（router 属性继承自 Routable）
    system_router.include_router(auth_controller.router)
    system_router.include_router(user_controller.router)
    # ... 其他控制器
    
    return system_router
```

**修改文件**:
- `pyproject.toml` - 添加 classy-fastapi 依赖
- `src/api/v1/auth_routes.py` → 创建 AuthController(Routable) 类
- `src/api/v1/user_routes.py` → 创建 UserController(Routable) 类
- `src/api/v1/role_routes.py` → 创建 RoleController(Routable) 类
- `src/api/v1/menu_routes.py` → 创建 MenuController(Routable) 类
- `src/api/v1/permission_routes.py` → 创建 PermissionController(Routable) 类
- `src/api/v1/system_routes.py` → 创建 SystemController(Routable) 类
- `src/api/v1/__init__.py` → 更新路由注册逻辑

**核心优势**:
1. **无全局变量** - 依赖通过构造函数注入，完全避免全局状态
2. **装饰器简洁** - 使用 `@get`, `@post`, `@put`, `@delete` 装饰器自动注册路由
3. **实例级别路由** - 路由绑定到实例而非类，支持灵活的依赖注入
4. **标准 FastAPI 兼容** - 完全兼容 FastAPI 的 Depends、Security 等机制
5. **代码减少 40%** - 消除样板代码，专注于业务逻辑
6. **易于测试** - 控制器实例化简单，便于单元测试
7. **成熟稳定** - 0.7.0 版本，支持 Python 3.9+，MIT 许可证

**与 FastAPI 官方实践对比**:

FastAPI 官方推荐（函数式）：
```python
router = APIRouter()

@router.get("/user/{user_id}")
async def get_user(user_id: str, service: UserService = Depends(get_user_service)):
    return await service.get_user(user_id)
```

classy-fastapi（面向对象）：
```python
class UserController(Routable):
    @get("/{user_id}")
    async def get_user(self, user_id: str, service: UserService = Depends(get_user_service)):
        return await service.get_user(user_id)
```

两者完全兼容，可以混合使用！

---

### Task 3: 优化依赖注入模式

**当前问题**: 
- `dependencies.py` 中服务工厂函数创建仓储时重复代码多
- 部分路由直接使用仓储而非服务层

**优化方案**:
```python
# src/api/dependencies.py
class ServiceFactory:
    """服务工厂类 - 统一管理依赖注入"""
    
    @staticmethod
    async def create_auth_service(
        db: AsyncSession = Depends(get_db),
        token_service: TokenService = Depends(get_token_service),
        password_service: PasswordService = Depends(get_password_service)
    ) -> AuthService:
        return AuthService(
            session=db,
            user_repo=UserRepository(db),
            role_repo=RoleRepository(db),
            perm_repo=PermissionRepository(db),
            token_service=token_service,
            password_service=password_service
        )
```

**修改文件**:
- `src/api/dependencies.py` - 创建 ServiceFactory 类
- 更新所有路由中的依赖注入

---

### Task 4: 完善异常处理和响应格式

**当前问题**:
- `src/api/common.py` 使用函数式响应格式化
- 异常处理分散

**优化方案**:
```python
# src/api/common.py
class APIResponse:
    """统一API响应类"""
    
    @staticmethod
    def success(data: Any = None, message: str = "成功", code: int = 0) -> dict:
        return {"code": code, "message": message, "data": data}
    
    @staticmethod
    def error(code: int, message: str) -> dict:
        return {"code": code, "message": message, "data": None}
```

**修改文件**:
- `src/api/common.py` - 改为 APIResponse 类
- 更新所有路由中的响应调用

---

### Task 5: 完善单元测试覆盖

**测试目标**: 80%+ 覆盖率，所有测试100%通过

**新增测试文件**:
- `tests/unit/test_menu_service.py` - 菜单服务测试
- `tests/unit/test_role_service.py` - 角色服务测试
- `tests/unit/test_department_service.py` - 部门服务测试
- `tests/unit/test_permission_service.py` - 权限服务测试
- `tests/unit/test_auth_service.py` - 认证服务测试
- `tests/unit/repositories/test_user_repository.py` - 用户仓储测试
- `tests/unit/repositories/test_menu_repository.py` - 菜单仓储测试

**修复现有测试**:
- `tests/unit/test_user_service.py` - 适配新的仓储接口
- `tests/integration/test_api.py` - 适配路由变更
- `tests/conftest.py` - 更新 fixtures

**测试覆盖模块**:
- Domain层: entities, services, repositories interfaces
- Application层: services, dto validators
- Infrastructure层: repositories implementations
- API层: routes (通过集成测试)

---

### Task 6: 代码质量优化

**优化项**:
1. 消除所有函数式编程（除 main.py 的 create_app）
2. 统一使用类型注解
3. 添加缺失的文档字符串
4. 优化导入顺序（使用 isort）
5. 确保符合 PEP8 和 FastAPI 最佳实践

**检查工具**:
```bash
ruff format src/ tests/
ruff check src/ tests/ --fix
pytest tests/ -v --cov=src --cov-report=term-missing
```

---

### Task 7: 更新项目文档

**更新文件**:
- `README.md` - 更新项目结构和运行说明
- `docs/design/项目架构设计与约束.md` - 更新架构设计文档

---

## 执行顺序

1. **Task 1** - 统一仓储层（基础，影响最广）
2. **Task 2** - 路由层面向对象封装
3. **Task 3** - 优化依赖注入
4. **Task 4** - 统一响应格式
5. **Task 5** - 完善测试（确保前面修改正确）
6. **Task 6** - 代码质量检查
7. **Task 7** - 文档更新

## 风险控制

- 每个 Task 完成后运行测试验证
- 使用 git commit 分步提交
- 保持向后兼容（API接口不变）
- 测试先行（TDD理念）

## 预期成果

1. 100% 面向对象（除入口函数）
2. 测试覆盖率 80%+
3. 所有测试 100% 通过
4. 符合 FastAPI 官方最佳实践
5. 清晰的 DDD 分层架构
6. 完善的文档和注释
