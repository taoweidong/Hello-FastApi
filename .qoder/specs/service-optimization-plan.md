# Service 后端代码优化计划

## Context

本计划旨在优化 Hello-FastApi 项目的 service 后端代码，在保持功能不变的前提下：
- 提升代码可维护性
- 减少重复代码
- 完善单元测试覆盖
- 更新文档并保持项目整洁

## 问题分析

### 1. 重复代码问题

#### 1.1 DTO 层重复的验证器
多个 DTO 文件中存在相同的验证逻辑：
- `user_dto.py`、`rbac_dto.py`、`menu_dto.py` 中都有 `empty_str_to_none` 和 `empty_str_or_zero_to_none` 验证器
- 相同代码重复出现 3-4 次

#### 1.2 仓储层重复的分页逻辑
- `user_repository.py`、`rbac_repository.py`、`log_repository.py` 中分页和筛选逻辑相似
- 缺少通用的基类或工具函数

#### 1.3 路由层重复的响应转换
- 多个路由文件中存在相似的数据转换逻辑
- `system_routes.py`、`user_routes.py`、`rbac_routes.py` 中列表转换模式重复

#### 1.4 日志服务重复的时间处理
- `log_service.py` 中三种日志的时间范围处理逻辑重复

### 2. 架构一致性问题

#### 2.1 仓储层接口缺失
- `DepartmentRepository` 和 `LogRepository` 没有实现接口
- 与 `UserRepository`、`RoleRepository` 的模式不一致

#### 2.2 MenuService 实现问题
- `MenuService.__init__` 中 `self.perm_repo = PermissionRepository` 是类引用而非实例
- 未按标准注入 session

### 3. 测试覆盖不足

#### 3.1 现有测试
- `test_auth.py`：密码和令牌服务的基础测试
- `test_api.py`：API 端点的集成测试

#### 3.2 缺失测试
- 服务层（Service）单元测试
- 仓储层（Repository）单元测试
- DTO 验证器测试
- 异常处理测试
- 边界条件测试

## 优化方案

### Phase 1: 提取公共组件，减少重复代码

#### 1.1 创建公共验证器模块
**文件**: `src/core/validators.py`（已存在，需要扩展）

添加通用验证器函数：
```python
def empty_str_to_none(v: str | None) -> str | None:
    """将空字符串转换为 None"""
    return None if v == '' else v

def empty_str_or_zero_to_none(v: int | str | None) -> int | None:
    """将空字符串或 0 转换为 None"""
    if v == '' or v == 0 or v is None:
        return None
    return int(v) if isinstance(v, str) else v
```

修改涉及文件：
- `src/application/dto/user_dto.py`
- `src/application/dto/rbac_dto.py`
- `src/application/dto/menu_dto.py`
- `src/application/dto/department_dto.py`

#### 1.2 创建仓储基类
**文件**: `src/infrastructure/repositories/base.py`（新建）

提供通用的分页、筛选和 CRUD 方法：
```python
class BaseRepository(Generic[ModelType]):
    """仓储基类，提供通用 CRUD 和分页功能"""
    
    async def get_by_id(self, id: str) -> ModelType | None
    async def get_all(self, page_num: int, page_size: int, ...) -> list[ModelType]
    async def count(self, ...) -> int
    async def create(self, entity: ModelType) -> ModelType
    async def update(self, entity: ModelType) -> ModelType
    async def delete(self, id: str) -> bool
    async def batch_delete(self, ids: list[str]) -> int
```

修改涉及文件：
- `src/infrastructure/repositories/user_repository.py`
- `src/infrastructure/repositories/rbac_repository.py`
- `src/infrastructure/repositories/menu_repository.py`
- `src/infrastructure/repositories/department_repository.py`
- `src/infrastructure/repositories/log_repository.py`

#### 1.3 创建响应转换工具
**文件**: `src/api/common.py`（已存在，需要扩展）

添加通用的模型转换函数：
```python
def model_to_dict(model, exclude_none: bool = False) -> dict
def models_to_list(models: list, exclude_none: bool = False) -> list[dict]
def timestamp_to_milliseconds(dt: datetime) -> int | None
```

修改涉及文件：
- `src/api/v1/user_routes.py`
- `src/api/v1/rbac_routes.py`
- `src/api/v1/menu_routes.py`
- `src/api/v1/system_routes.py`

### Phase 2: 统一架构模式

#### 2.1 添加缺失的仓储接口
**文件**: `src/domain/department/repository.py`（新建）
**文件**: `src/domain/log/repository.py`（新建）

定义接口：
```python
class DepartmentRepositoryInterface(Protocol):
    async def get_by_id(self, dept_id: str, session: AsyncSession) -> Department | None: ...
    async def get_by_name(self, name: str, session: AsyncSession) -> Department | None: ...
    # ...其他方法

class LogRepositoryInterface(Protocol):
    async def get_login_logs(...) -> tuple[list[LoginLog], int]: ...
    # ...其他方法
```

#### 2.2 修复 MenuService
**文件**: `src/application/services/menu_service.py`

修改内容：
- 将 `session` 作为构造函数参数注入
- 修复 `self.perm_repo` 为实例引用
- 保持与其他 Service 一致的架构模式

### Phase 3: 完善单元测试

#### 3.1 服务层测试
**文件**: `tests/unit/test_user_service.py`（新建）
**文件**: `tests/unit/test_rbac_service.py`（新建）
**文件**: `tests/unit/test_auth_service.py`（新建）
**文件**: `tests/unit/test_menu_service.py`（新建）
**文件**: `tests/unit/test_department_service.py`（新建）
**文件**: `tests/unit/test_log_service.py`（新建）

测试内容：
- 正常流程测试
- 异常处理测试
- 边界条件测试

#### 3.2 仓储层测试
**文件**: `tests/unit/test_repositories.py`（新建）

测试内容：
- CRUD 操作
- 分页和筛选
- 关联查询

#### 3.3 DTO 验证器测试
**文件**: `tests/unit/test_dto_validators.py`（新建）

测试内容：
- 验证器逻辑
- 边界值测试

### Phase 4: 更新文档

#### 4.1 更新 README.md
**文件**: `service/README.md`

更新内容：
- 添加新的测试说明
- 更新代码结构说明
- 添加新的开发规范

#### 4.2 更新 API 文档
确保所有接口的文档字符串完整准确。

## 涉及文件清单

### 新建文件
1. `src/infrastructure/repositories/base.py` - 仓储基类
2. `src/domain/department/repository.py` - 部门仓储接口
3. `src/domain/log/repository.py` - 日志仓储接口
4. `tests/unit/test_user_service.py` - 用户服务测试
5. `tests/unit/test_rbac_service.py` - RBAC 服务测试
6. `tests/unit/test_auth_service.py` - 认证服务测试
7. `tests/unit/test_menu_service.py` - 菜单服务测试
8. `tests/unit/test_department_service.py` - 部门服务测试
9. `tests/unit/test_log_service.py` - 日志服务测试
10. `tests/unit/test_repositories.py` - 仓储层测试
11. `tests/unit/test_dto_validators.py` - DTO 验证器测试

### 修改文件
1. `src/core/validators.py` - 扩展通用验证器
2. `src/api/common.py` - 扩展响应转换工具
3. `src/application/dto/user_dto.py` - 使用公共验证器
4. `src/application/dto/rbac_dto.py` - 使用公共验证器
5. `src/application/dto/menu_dto.py` - 使用公共验证器
6. `src/application/dto/department_dto.py` - 使用公共验证器
7. `src/infrastructure/repositories/user_repository.py` - 继承基类
8. `src/infrastructure/repositories/rbac_repository.py` - 继承基类
9. `src/infrastructure/repositories/menu_repository.py` - 继承基类
10. `src/infrastructure/repositories/department_repository.py` - 实现接口
11. `src/infrastructure/repositories/log_repository.py` - 实现接口
12. `src/application/services/menu_service.py` - 修复架构问题
13. `src/application/services/log_service.py` - 提取公共逻辑
14. `src/api/v1/user_routes.py` - 使用公共转换工具
15. `src/api/v1/rbac_routes.py` - 使用公共转换工具
16. `src/api/v1/menu_routes.py` - 使用公共转换工具
17. `src/api/v1/system_routes.py` - 使用公共转换工具
18. `service/README.md` - 更新文档

## 验证方案

### 1. 代码质量验证
```bash
cd service
ruff check src/
ruff format src/
mypy src/
```

### 2. 测试验证
```bash
cd service
pytest -v
pytest --cov=src --cov-report=term-missing
```

### 3. 功能验证
```bash
# 启动服务
python -m scripts.cli runserver

# 验证 API 端点
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/system/login -d '{"username":"admin","password":"xxx"}'
```

## 实施顺序

1. **Phase 1**: 提取公共组件（低风险，高收益）
2. **Phase 2**: 统一架构模式（中等风险）
3. **Phase 3**: 完善单元测试（低风险）
4. **Phase 4**: 更新文档（低风险）

## 风险评估

- **低风险**: 公共验证器提取、测试编写、文档更新
- **中等风险**: 仓储基类重构、MenuService 修改
- **缓解措施**: 
  - 每个阶段完成后运行完整测试
  - 保持向后兼容
  - 逐步重构，不一次性大改
