# 对齐 pure-admin-backend API 改造计划

## 差异总览

| 维度 | 当前项目 | pure-admin-backend | 改造方向 |
|------|---------|-------------------|---------|
| 响应格式 | 直接返回数据对象 / `{"detail":"..."}` | `{"code":200,"message":"...","data":{...}}` | 统一包装 |
| API前缀 | `/api/v1/auth`, `/api/v1/users`, `/api/v1/rbac` | `/api/system/` 统一前缀 | 路由重构 |
| 分页参数 | `skip/limit` query params | `pageNum/pageSize` body/params, 响应含 `rows/totalPage` | 全面改造 |
| 字段命名 | snake_case (`access_token`, `created_at`) | camelCase (`accessToken`, `createTime`) | DTO别名 |
| 权限编码 | `user.view` (点分隔) | `user:view` (冒号分隔) | 全局替换 |
| 用户模型 | `full_name`, `is_active`, `is_superuser` | `nickname`, `avatar`, `phone`, `sex`, `status`(0/1), `remark` | 扩展字段 |
| 角色模型 | 仅 `name`, `description` | 增加 `code`, `status` | 扩展字段 |
| 权限模型 | `codename`, `resource`, `action` | `code`, `category`, `status` | 字段重命名 |
| 菜单管理 | 无 | 完整CRUD + 菜单树 | 新增模块 |
| 缺失接口 | - | 注册、登出、批量删除、重置密码、状态切换等 | 新增 |

---

## Task 1: 统一响应格式封装

**目标**: 创建统一响应包装器，所有 API 返回 `{code, message, data}` 格式。

**修改文件**:
- `src/api/common.py` — 新增 `UnifiedResponse` 模型和 `success_response()` / `error_response()` 工具函数
- `src/core/exceptions.py` — 异常响应格式从 `{"detail":"..."}` 改为 `{"code":xxx, "message":"..."}`
- `src/main.py` — 修改全局异常处理器，使用统一格式

**响应模型**:
```python
class UnifiedResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Any = None
```

**分页响应模型**:
```python
class PageResponse(BaseModel):
    total: int
    pageNum: int
    pageSize: int
    totalPage: int
    rows: list
```

---

## Task 2: API 路由前缀重构

**目标**: 将路由前缀从 `/api/v1/` 改为 `/api/system/`。

**修改文件**:
- `src/main.py` — 修改路由注册，前缀改为 `/api/system`
- `src/api/v1/auth_routes.py` — 路由前缀调整
- `src/api/v1/user_routes.py` — 路由前缀调整为 `/user`
- `src/api/v1/rbac_routes.py` — 拆分为 `/role` 和 `/permission` 子路由
- `src/core/constants.py` — 更新 `API_PREFIX` / `API_V1_PREFIX` 常量

**路由映射**:
| 旧路径 | 新路径 |
|--------|--------|
| `/api/v1/auth/login` | `/api/system/login` |
| `/api/v1/auth/refresh` | `/api/system/refresh` |
| `/api/v1/auth/me` | `/api/system/user/info` |
| `/api/v1/users/` | `/api/system/user` |
| `/api/v1/users/{id}` | `/api/system/user/{id}` |
| `/api/v1/rbac/roles` | `/api/system/role` |
| `/api/v1/rbac/permissions` | `/api/system/permission` |

---

## Task 3: 数据模型扩展

**目标**: 扩展 User、Role、Permission 模型字段以对齐 pure-admin。

**修改文件**:
- `src/infrastructure/database/models.py`

**User 模型变更**:
- 保留: `id`, `username`, `email`, `hashed_password`, `created_at`, `updated_at`
- 新增: `nickname`(str), `avatar`(str), `phone`(str), `sex`(int, 0/1), `status`(int, 0禁用/1启用), `dept_id`(int), `remark`(str)
- 调整: `is_active` 逻辑迁移到 `status` 字段 (1=启用, 0=禁用)，保留 `is_superuser`

**Role 模型变更**:
- 新增: `code`(str, unique), `status`(int, 默认1)
- 保留: `id`, `name`, `description`, `created_at`
- 新增: `updated_at`

**Permission 模型变更**:
- 重命名: `codename` → `code`
- 新增: `category`(str), `status`(int, 默认1)
- 移除/保留: `resource`, `action` 可保留做内部使用

---

## Task 4: DTO 层全面改造

**目标**: 更新所有 DTO 的字段名和结构，响应字段使用 camelCase 别名。

**修改文件**:
- `src/application/dto/auth_dto.py`
- `src/application/dto/user_dto.py`
- `src/application/dto/rbac_dto.py`
- 新增: `src/application/dto/menu_dto.py`

**关键变更**:
- 登录响应: `TokenResponseDTO` → 含 `accessToken`, `expires`(秒), `refreshToken`, `userInfo`, `roles`, `permissions`
- 用户DTO: 新增 `nickname`, `avatar`, `phone`, `sex`, `status`, `remark` 字段；响应字段用 camelCase 别名 (`createTime`, `updateTime`)
- 角色DTO: 新增 `code`, `status` 字段
- 权限DTO: `codename` → `code`, 新增 `category`, `status`
- 分页请求DTO: 新增 `PageQueryDTO(pageNum, pageSize, sortBy, sortOrder)`

---

## Task 5: 认证模块改造

**目标**: 认证接口对齐 pure-admin（登录/注册/登出/刷新/用户信息）。

**修改文件**:
- `src/api/v1/auth_routes.py` — 修改路由和响应
- `src/application/services/auth_service.py` — 登录逻辑返回完整用户信息
- `src/domain/auth/token_service.py` — `expires` 值调整

**新增接口**:
- `POST /api/system/register` — 用户注册
- `POST /api/system/logout` — 用户登出

**修改接口**:
- `POST /api/system/login` — 响应增加 `userInfo`、`roles`、`permissions`
- `POST /api/system/refresh` — 响应改为 `{accessToken, expires, refreshToken}`
- `GET /api/system/user/info` — 替代原 `/auth/me`，返回完整用户信息含角色和权限

---

## Task 6: 用户管理模块改造

**目标**: 用户 CRUD 接口对齐 pure-admin 格式，新增缺失接口。

**修改文件**:
- `src/api/v1/user_routes.py`
- `src/application/services/user_service.py`
- `src/infrastructure/repositories/user_repository.py`

**修改接口**:
- `POST /api/system/user/list` — 改为 POST + body 分页查询（含 username/phone/status 等筛选条件）
- `POST /api/system/user` — 创建用户（新增字段）
- `GET /api/system/user/{id}` — 获取详情（含角色、权限信息）
- `PUT /api/system/user/{id}` — 更新用户（扩展字段）
- `DELETE /api/system/user/{id}` — 删除用户

**新增接口**:
- `POST /api/system/user/batch-delete` — 批量删除
- `PUT /api/system/user/{id}/reset-password` — 管理员重置密码
- `PUT /api/system/user/{id}/status` — 更改用户状态

**保留接口**（路径调整）:
- `POST /api/system/user/change-password` — 当前用户修改自己密码（对应原 `/me/change-password`）

---

## Task 7: RBAC 模块改造

**目标**: 角色和权限管理接口对齐 pure-admin。

**修改文件**:
- `src/api/v1/rbac_routes.py`
- `src/application/services/rbac_service.py`
- `src/infrastructure/repositories/rbac_repository.py`
- `src/application/dto/rbac_dto.py`

**角色接口改造**:
- `GET /api/system/role/list` — 分页角色列表
- `POST /api/system/role` — 创建角色（含 code 字段）
- `PUT /api/system/role/{id}` — 更新角色
- `DELETE /api/system/role/{id}` — 删除角色
- `POST /api/system/role/{roleId}/permissions` — 为角色分配权限（新增）

**权限接口改造**:
- `GET /api/system/permission/list` — 分页权限列表
- `POST /api/system/permission` — 创建权限（含 code, category）
- `DELETE /api/system/permission/{id}` — 删除权限

**移除/重构**:
- 原 `/rbac/assign-role`, `/rbac/remove-role` → 改为通过更新用户时传递 roleIds 或独立接口
- 原 `/rbac/users/{id}/roles`, `/rbac/users/{id}/permissions` → 合并到用户详情接口

**权限编码格式**:
- 全局从 `user.view` 改为 `user:view` 冒号分隔

---

## Task 8: 新增菜单管理模块

**目标**: 全新实现菜单管理功能，包含数据模型、仓储、服务、DTO、路由。

**新增文件**:
- `src/infrastructure/database/models.py` — 新增 `Menu` 实体（id, name, path, component, icon, title, show_link, parent_id, order_num, permissions, status, created_at, updated_at）
- `src/domain/menu/` — 新增目录
- `src/domain/menu/__init__.py`
- `src/domain/menu/repository.py` — 菜单仓储接口
- `src/infrastructure/repositories/menu_repository.py` — 菜单仓储实现
- `src/application/dto/menu_dto.py` — 菜单 DTO
- `src/application/services/menu_service.py` — 菜单业务逻辑
- `src/api/v1/menu_routes.py` — 菜单路由

**API 接口**:
- `GET /api/system/menu/tree` — 获取完整菜单树
- `GET /api/system/menu/user-menus` — 获取当前用户可访问菜单
- `POST /api/system/menu` — 创建菜单
- `PUT /api/system/menu/{id}` — 更新菜单
- `DELETE /api/system/menu/{id}` — 删除菜单

---

## Task 9: 权限依赖与常量更新

**目标**: 更新权限编码格式和相关依赖注入。

**修改文件**:
- `src/core/constants.py` — 权限编码从 `user.view` 改为 `user:view`，新增菜单相关权限
- `src/api/dependencies.py` — 权限检查逻辑适配新格式
- 所有路由文件中引用权限编码的地方统一更新

**新增权限**:
- `menu:view`, `menu:add`, `menu:edit`, `menu:delete`

---

## Task 10: 测试更新

**目标**: 更新测试用例以适配新的 API 接口和响应格式。

**修改文件**:
- `tests/unit/test_auth.py`
- `tests/unit/test_core.py`
- `tests/integration/test_api.py`
- `tests/conftest.py`

---

## 执行顺序

```
Task 1 (统一响应格式) ──┐
Task 3 (数据模型扩展) ──┤
Task 9 (权限常量更新) ──┼──> Task 2 (路由重构) ──> Task 5 (认证改造)
Task 4 (DTO改造)    ──┘                      ──> Task 6 (用户改造)
                                              ──> Task 7 (RBAC改造)
                                              ──> Task 8 (菜单模块)
                                              ──> Task 10 (测试更新)
```

Task 1/3/4/9 为基础改造，可并行执行；Task 2 依赖 Task 1 完成；Task 5-8 依赖 Task 2/3/4 完成；Task 10 最后执行。
