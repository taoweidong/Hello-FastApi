---
name: fix-n1-query-permission-check
overview: 修复 require_permission 权限检查中的 N+1 查询问题，通过新增批量查询方法将 N+1 次查询优化为 1 次查询。
todos:
  - id: add-repo-method
    content: 在 RoleRepository 接口和实现中新增 get_user_all_menus 方法
    status: completed
  - id: fix-auth-deps
    content: 重构 auth.py 中 require_permission 和 require_menu_permission 消除 N+1 查询
    status: completed
    dependencies:
      - add-repo-method
  - id: fix-auth-service
    content: 重构 auth_service.py 中 login 和 get_async_routes 消除 N+1 查询
    status: completed
    dependencies:
      - add-repo-method
---

## 产品概述

修复权限检查中的 N+1 查询性能问题，将每次权限验证的数据库查询次数从 N+1 降至 1 次。

## 核心功能

- 在 RoleRepository 中新增 `get_user_all_menus(user_id)` 方法，通过一次三表 JOIN 查询（UserRole → RoleMenuLink → Menu）直接获取用户所有角色关联的菜单，替代逐角色循环查询
- 重构 `require_permission()` 和 `require_menu_permission()` 中的 N+1 查询逻辑，使用新方法
- 重构 `AuthService.login()` 和 `AuthService.get_async_routes()` 中同样存在的 N+1 查询，统一使用新方法
- 保持缓存机制不变，仅优化缓存未命中时的数据库查询路径

## 技术栈

- 框架: FastAPI + SQLModel + SQLAlchemy（复用现有项目技术栈）
- 数据库: MySQL/SQLite（通过 SQLModel AsyncSession 抽象）
- 缓存: Redis（已有权限缓存，TTL 5 分钟）

## 实现方案

### 核心策略

新增 `get_user_all_menus(user_id)` 方法，通过一次三表 JOIN（`sys_userinfo_roles` JOIN `sys_userrole_menu` JOIN `sys_menus`）直接获取用户所有角色关联的去重菜单列表，将 N+1 次查询降为 1 次。

### 关键技术决策

1. **单次 JOIN 查询替代循环查询**：SQL 语句为 `SELECT DISTINCT Menu.* FROM sys_userinfo_roles JOIN sys_userrole_menu ON ... JOIN sys_menus ON ... WHERE UserRole.userinfo_id = :user_id`，一次查询完成所有数据获取
2. **使用 `selectinload` 加载 Menu.meta**：与现有 `get_role_menus` 保持一致，确保 `to_domain()` 转换不出错
3. **应用层去重**：SQL 层面可使用 `DISTINCT`，但 `selectinload` 可能与 `DISTINCT` 冲突，因此采用 Python 层 `seen_ids` 集合去重，与 `auth_service.py` 中现有模式保持一致
4. **保持缓存逻辑不变**：缓存命中路径零查询，缓存未命中路径从 N+1 降为 1 次，缓存写入逻辑不变

### 性能分析

- **优化前**: 缓存未命中时 1（查角色）+ N（逐角色查菜单）= N+1 次查询，5 个角色 = 6 次查询
- **优化后**: 缓存未命中时 1 次查询，无论多少角色
- **缓存命中**: 0 次查询（不变）
- **影响范围**: `require_permission`、`require_menu_permission`、`login`、`get_async_routes` 四处 N+1 均被消除

## 实现注意事项

- `Menu` ORM 模型有 `meta` 关系（`selectinload`），新查询必须 `options(selectinload(Menu.meta))`，否则 `to_domain()` 中 `self.meta.to_domain()` 会报错
- `UserRole.userinfo_id` 和 `RoleMenuLink.userrole_id` 是关联字段名，JOIN 时注意字段匹配
- `auth_service.py` 中 `login()` 和 `get_async_routes()` 两处都需要修改，统一使用新方法
- `auth.py` 中 `require_permission` 和 `require_menu_permission` 两处 N+1 逻辑需同时修改
- 遵循 DDD 分层约束：接口定义在 `domain/repositories`，实现在 `infrastructure/repositories`

## 架构设计

修改仅涉及仓储层和应用层，不改变领域实体和缓存机制：

```
auth.py (API层) ──调用──→ RoleRepository.get_user_all_menus(user_id)
                                     │
auth_service.py (应用层) ──调用──→ ──┘
                                     │
                            单次 JOIN 查询:
                            UserRole → RoleMenuLink → Menu
                            (替代: get_user_roles + N×get_role_menus)
```

## 目录结构

```
service/src/
├── domain/repositories/role_repository.py        # [MODIFY] 新增 get_user_all_menus 抽象方法
├── infrastructure/repositories/role_repository.py # [MODIFY] 实现 get_user_all_menus，一次三表 JOIN 查询
├── api/dependencies/auth.py                      # [MODIFY] require_permission 和 require_menu_permission 使用新方法替代循环
└── application/services/auth_service.py           # [MODIFY] login 和 get_async_routes 使用新方法替代循环
```