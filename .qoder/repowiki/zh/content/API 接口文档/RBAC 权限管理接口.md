# RBAC 权限管理接口

<cite>
**本文引用的文件**
- [rbac_routes.py](file://service/src/api/v1/rbac_routes.py)
- [rbac_service.py](file://service/src/application/services/rbac_service.py)
- [rbac_dto.py](file://service/src/application/dto/rbac_dto.py)
- [rbac_repository.py](file://service/src/infrastructure/repositories/rbac_repository.py)
- [models.py](file://service/src/infrastructure/database/models.py)
- [dependencies.py](file://service/src/api/dependencies.py)
- [menu_routes.py](file://service/src/api/v1/menu_routes.py)
- [menu_service.py](file://service/src/application/services/menu_service.py)
- [redis_client.py](file://service/src/infrastructure/cache/redis_client.py)
- [decorators.py](file://service/src/core/decorators.py)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考量](#性能考量)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本文件为 RBAC 权限管理接口的权威文档，覆盖角色管理、权限管理、角色权限分配以及用户角色分配的完整 API。文档同时阐述权限继承与权限验证机制、权限树形结构数据格式与查询方法、动态权限控制原理与实现、权限缓存策略与性能优化建议，并给出最佳实践与安全注意事项。

## 项目结构
RBAC 子系统采用分层架构：
- API 层：定义路由与依赖校验，负责参数解析与统一响应包装
- 应用服务层：编排业务流程，协调仓储与 DTO
- 领域仓储接口层：定义角色与权限的抽象操作契约
- 基础设施仓储实现层：基于 SQLModel 的具体数据库操作
- 数据模型层：定义角色、权限、用户角色关联等实体
- 依赖注入与中间件：鉴权、权限校验、日志装饰器等

```mermaid
graph TB
subgraph "API 层"
R["rbac_routes.py<br/>角色/权限路由"]
M["menu_routes.py<br/>菜单路由"]
end
subgraph "应用服务层"
S["rbac_service.py<br/>RBACService"]
MS["menu_service.py<br/>MenuService"]
end
subgraph "仓储接口层"
RI["rbac_repository.py<br/>RoleRepositoryInterface/PermissionRepositoryInterface"]
end
subgraph "仓储实现层"
RP["rbac_repository.py<br/>RoleRepository/PermissionRepository"]
end
subgraph "数据模型层"
DM["models.py<br/>Role/Permission/UserRole/RolePermissionLink"]
end
subgraph "依赖与工具"
D["dependencies.py<br/>require_permission/get_current_active_user"]
RC["redis_client.py<br/>Redis 客户端"]
DEC["decorators.py<br/>log_execution"]
end
R --> S
M --> MS
S --> RI
MS --> RI
RI --> RP
RP --> DM
D --> S
D --> MS
DEC --> S
DEC --> MS
RC -. 可选缓存 .-> S
```

图表来源
- [rbac_routes.py:1-257](file://service/src/api/v1/rbac_routes.py#L1-L257)
- [menu_routes.py:1-71](file://service/src/api/v1/menu_routes.py#L1-L71)
- [rbac_service.py:1-231](file://service/src/application/services/rbac_service.py#L1-L231)
- [menu_service.py:1-169](file://service/src/application/services/menu_service.py#L1-L169)
- [rbac_repository.py:1-213](file://service/src/infrastructure/repositories/rbac_repository.py#L1-L213)
- [models.py:1-193](file://service/src/infrastructure/database/models.py#L1-L193)
- [dependencies.py:1-72](file://service/src/api/dependencies.py#L1-L72)
- [redis_client.py:1-24](file://service/src/infrastructure/cache/redis_client.py#L1-L24)
- [decorators.py:1-24](file://service/src/core/decorators.py#L1-L24)

章节来源
- [rbac_routes.py:1-257](file://service/src/api/v1/rbac_routes.py#L1-L257)
- [rbac_service.py:1-231](file://service/src/application/services/rbac_service.py#L1-L231)
- [rbac_repository.py:1-213](file://service/src/infrastructure/repositories/rbac_repository.py#L1-L213)
- [models.py:1-193](file://service/src/infrastructure/database/models.py#L1-L193)
- [dependencies.py:1-72](file://service/src/api/dependencies.py#L1-L72)
- [menu_routes.py:1-71](file://service/src/api/v1/menu_routes.py#L1-L71)
- [menu_service.py:1-169](file://service/src/application/services/menu_service.py#L1-L169)
- [redis_client.py:1-24](file://service/src/infrastructure/cache/redis_client.py#L1-L24)
- [decorators.py:1-24](file://service/src/core/decorators.py#L1-L24)

## 核心组件
- 角色管理：创建、查询、更新、删除角色；角色详情含权限列表
- 权限管理：创建、查询、删除权限；支持按名称模糊查询
- 角色权限分配：为角色批量分配权限，先清空旧关联再建立新关联
- 用户角色分配：为用户分配/移除角色；获取用户角色与权限集合
- 权限验证：基于用户权限编码进行动态校验
- 菜单权限集成：菜单与权限编码关联，按用户权限过滤菜单树

章节来源
- [rbac_routes.py:33-177](file://service/src/api/v1/rbac_routes.py#L33-L177)
- [rbac_service.py:28-199](file://service/src/application/services/rbac_service.py#L28-L199)
- [rbac_repository.py:84-134](file://service/src/infrastructure/repositories/rbac_repository.py#L84-L134)
- [dependencies.py:45-61](file://service/src/api/dependencies.py#L45-L61)
- [menu_routes.py:19-36](file://service/src/api/v1/menu_routes.py#L19-L36)
- [menu_service.py:27-51](file://service/src/application/services/menu_service.py#L27-L51)

## 架构总览
RBAC 请求处理链路如下：
- 路由接收请求，参数校验与分页参数解析
- 依赖注入完成鉴权与权限校验
- 应用服务编排业务逻辑，调用仓储层持久化
- 返回统一响应格式

```mermaid
sequenceDiagram
participant C as "客户端"
participant R as "rbac_routes.py"
participant D as "dependencies.py"
participant S as "rbac_service.py"
participant P as "PermissionRepository"
participant RL as "RoleRepository"
participant DB as "数据库"
C->>R : "POST /api/system/role/{role_id}/permissions"
R->>D : "require_permission('role : manage')"
D->>P : "get_user_permissions(user_id)"
P->>DB : "查询用户权限"
DB-->>P : "权限列表"
P-->>D : "权限编码集合"
D-->>R : "校验通过/抛出异常"
R->>S : "assign_permissions(role_id, permissionIds)"
S->>RL : "assign_permissions_to_role(role_id, ids)"
RL->>DB : "删除旧关联并插入新关联"
DB-->>RL : "写入完成"
RL-->>S : "成功"
S-->>R : "返回成功"
R-->>C : "统一响应"
```

图表来源
- [rbac_routes.py:154-177](file://service/src/api/v1/rbac_routes.py#L154-L177)
- [dependencies.py:45-61](file://service/src/api/dependencies.py#L45-L61)
- [rbac_service.py:121-129](file://service/src/application/services/rbac_service.py#L121-L129)
- [rbac_repository.py:84-96](file://service/src/infrastructure/repositories/rbac_repository.py#L84-L96)

## 详细组件分析

### 角色管理接口
- 列表查询（分页）
  - 方法与路径：GET /api/system/role/list
  - 查询参数：pageNum、pageSize、roleName（模糊）、status
  - 权限要求：role:view
  - 行为：调用服务层获取角色列表与总数，统一分页响应
- 新增角色
  - 方法与路径：POST /api/system/role/
  - 请求体：RoleCreateDTO（name/code/description/status/permissionIds）
  - 权限要求：role:manage
  - 行为：校验唯一性后创建角色，可选分配权限
- 获取角色详情
  - 方法与路径：GET /api/system/role/{role_id}
  - 路径参数：role_id
  - 权限要求：role:view
  - 行为：返回角色详情及权限列表（仅 id/code）
- 更新角色
  - 方法与路径：PUT /api/system/role/{role_id}
  - 路径参数：role_id
  - 请求体：RoleUpdateDTO（name/code/description/status/permissionIds）
  - 权限要求：role:manage
  - 行为：更新基础信息与权限（可选），权限为空时不变更
- 删除角色
  - 方法与路径：DELETE /api/system/role/{role_id}
  - 权限要求：role:manage
  - 行为：删除角色（不级联删除权限）

章节来源
- [rbac_routes.py:33-152](file://service/src/api/v1/rbac_routes.py#L33-L152)
- [rbac_service.py:28-120](file://service/src/application/services/rbac_service.py#L28-L120)
- [rbac_dto.py:8-46](file://service/src/application/dto/rbac_dto.py#L8-L46)

### 权限管理接口
- 列表查询（分页）
  - 方法与路径：GET /api/system/permission/list
  - 查询参数：pageNum、pageSize、permissionName（模糊）
  - 权限要求：permission:view
  - 行为：返回权限列表与总数
- 新增权限
  - 方法与路径：POST /api/system/permission/
  - 请求体：PermissionCreateDTO（name/code/category/description/status）
  - 权限要求：permission:manage
  - 行为：校验权限编码唯一性后创建
- 删除权限
  - 方法与路径：DELETE /api/system/permission/{permission_id}
  - 权限要求：permission:manage
  - 行为：删除权限

章节来源
- [rbac_routes.py:186-257](file://service/src/api/v1/rbac_routes.py#L186-L257)
- [rbac_service.py:133-165](file://service/src/application/services/rbac_service.py#L133-L165)
- [rbac_dto.py:48-75](file://service/src/application/dto/rbac_dto.py#L48-L75)

### 角色权限分配接口
- 为角色分配权限
  - 方法与路径：POST /api/system/role/{role_id}/permissions
  - 请求体：AssignPermissionsDTO（permissionIds）
  - 权限要求：role:manage
  - 行为：先清理旧关联，再批量插入新关联

章节来源
- [rbac_routes.py:154-177](file://service/src/api/v1/rbac_routes.py#L154-L177)
- [rbac_service.py:121-129](file://service/src/application/services/rbac_service.py#L121-L129)
- [rbac_dto.py:85-88](file://service/src/application/dto/rbac_dto.py#L85-L88)
- [rbac_repository.py:84-96](file://service/src/infrastructure/repositories/rbac_repository.py#L84-L96)

### 用户角色分配与权限查询接口
- 为用户分配角色
  - 方法与路径：POST /api/system/user/{user_id}/roles
  - 请求体：AssignRoleDTO（userId/roleId）
  - 权限要求：role:manage
  - 行为：若未分配则创建关联，否则冲突
- 移除用户角色
  - 方法与路径：DELETE /api/system/user/{user_id}/roles/{role_id}
  - 权限要求：role:manage
  - 行为：删除用户角色关联
- 获取用户角色
  - 方法与路径：GET /api/system/user/{user_id}/roles
  - 权限要求：role:view
  - 行为：返回用户角色列表
- 获取用户权限
  - 方法与路径：GET /api/system/user/{user_id}/permissions
  - 权限要求：permission:view
  - 行为：返回用户通过角色继承的权限列表
- 检查用户权限
  - 方法与路径：GET /api/system/user/{user_id}/check-permission/{codename}
  - 权限要求：permission:view
  - 行为：返回布尔值表示是否拥有指定权限编码

章节来源
- [rbac_service.py:169-199](file://service/src/application/services/rbac_service.py#L169-L199)
- [rbac_repository.py:107-134](file://service/src/infrastructure/repositories/rbac_repository.py#L107-L134)
- [rbac_routes.py:1-257](file://service/src/api/v1/rbac_routes.py#L1-L257)

### 权限继承与权限验证
- 继承机制
  - 用户通过用户-角色关联获得角色
  - 角色通过角色-权限关联获得权限
  - 用户权限 = 角色权限的并集
- 动态验证
  - 通过 require_permission 依赖在路由层拦截
  - 在仓储层查询用户权限编码集合，匹配目标权限编码
  - 超级用户豁免权限校验

```mermaid
flowchart TD
Start(["进入受保护路由"]) --> GetToken["解析并验证 JWT"]
GetToken --> GetUser["加载当前活跃用户"]
GetUser --> Superuser{"是否超级用户?"}
Superuser --> |是| Allow["放行"]
Superuser --> |否| LoadPerms["查询用户权限编码集合"]
LoadPerms --> Match{"目标权限编码存在于集合?"}
Match --> |是| Allow
Match --> |否| Deny["拒绝访问"]
Allow --> End(["结束"])
Deny --> End
```

图表来源
- [dependencies.py:45-61](file://service/src/api/dependencies.py#L45-L61)
- [rbac_repository.py:203-212](file://service/src/infrastructure/repositories/rbac_repository.py#L203-L212)

章节来源
- [dependencies.py:45-61](file://service/src/api/dependencies.py#L45-L61)
- [rbac_repository.py:203-212](file://service/src/infrastructure/repositories/rbac_repository.py#L203-L212)

### 权限树形结构与菜单权限
- 菜单树获取
  - 方法与路径：GET /api/system/menu/tree
  - 权限要求：menu:view
  - 行为：返回完整菜单树（父子关系）
- 用户可访问菜单
  - 方法与路径：GET /api/system/menu/user-menus
  - 权限要求：menu:view
  - 行为：根据用户权限过滤菜单，返回可访问的菜单树
- 菜单与权限关联
  - 菜单实体包含 permissions 字段，存储逗号分隔的权限编码
  - 用户访问菜单需满足“无关联权限”或“与用户权限集合有交集”

```mermaid
sequenceDiagram
participant C as "客户端"
participant MR as "menu_routes.py"
participant MS as "menu_service.py"
participant PR as "PermissionRepository"
participant DB as "数据库"
C->>MR : "GET /api/system/menu/user-menus"
MR->>MS : "get_user_menus(user_id)"
MS->>PR : "get_user_permissions(user_id)"
PR->>DB : "查询用户权限"
DB-->>PR : "权限列表"
PR-->>MS : "权限编码集合"
MS-->>MR : "过滤后的菜单树"
MR-->>C : "统一响应"
```

图表来源
- [menu_routes.py:29-36](file://service/src/api/v1/menu_routes.py#L29-L36)
- [menu_service.py:27-51](file://service/src/application/services/menu_service.py#L27-L51)
- [rbac_repository.py:203-212](file://service/src/infrastructure/repositories/rbac_repository.py#L203-L212)

章节来源
- [menu_routes.py:19-36](file://service/src/api/v1/menu_routes.py#L19-L36)
- [menu_service.py:22-51](file://service/src/application/services/menu_service.py#L22-L51)
- [models.py:146-171](file://service/src/infrastructure/database/models.py#L146-L171)

### 数据模型与关系
```mermaid
erDiagram
USERS {
string id PK
string username UK
string email
string hashed_password
int status
boolean is_superuser
}
ROLES {
string id PK
string name UK
string code UK
int status
}
PERMISSIONS {
string id PK
string name
string code UK
string category
int status
}
ROLE_PERMISSION_LINK {
string role_id PK
string permission_id PK
}
USER_ROLES {
string id PK
string user_id FK
string role_id FK
}
USERS ||--o{ USER_ROLES : "拥有"
USER_ROLES }o--o{ ROLES : "分配"
ROLES ||--o{ ROLE_PERMISSION_LINK : "授予"
ROLE_PERMISSION_LINK }o--o{ PERMISSIONS : "对应"
```

图表来源
- [models.py:31-141](file://service/src/infrastructure/database/models.py#L31-L141)
- [rbac_repository.py:17-26](file://service/src/infrastructure/repositories/rbac_repository.py#L17-L26)

章节来源
- [models.py:17-141](file://service/src/infrastructure/database/models.py#L17-L141)

## 依赖分析
- 路由到服务：各路由依赖 RBACService 执行业务逻辑
- 服务到仓储：RBACService 通过 RoleRepository 与 PermissionRepository 访问数据库
- 仓储到模型：SQLModel 定义实体与多对多关联表
- 权限校验：require_permission 依赖 TokenService 解析 JWT 并查询用户权限
- 日志装饰：log_execution 记录函数执行情况，便于问题定位

```mermaid
graph LR
R["rbac_routes.py"] --> S["rbac_service.py"]
S --> RR["RoleRepository"]
S --> PR["PermissionRepository"]
RR --> M["models.py"]
PR --> M
D["dependencies.py"] --> PR
DEC["decorators.py"] --> S
```

图表来源
- [rbac_routes.py:1-257](file://service/src/api/v1/rbac_routes.py#L1-L257)
- [rbac_service.py:1-231](file://service/src/application/services/rbac_service.py#L1-L231)
- [rbac_repository.py:1-213](file://service/src/infrastructure/repositories/rbac_repository.py#L1-L213)
- [models.py:1-193](file://service/src/infrastructure/database/models.py#L1-L193)
- [dependencies.py:1-72](file://service/src/api/dependencies.py#L1-L72)
- [decorators.py:1-24](file://service/src/core/decorators.py#L1-L24)

章节来源
- [rbac_routes.py:1-257](file://service/src/api/v1/rbac_routes.py#L1-L257)
- [rbac_service.py:1-231](file://service/src/application/services/rbac_service.py#L1-L231)
- [rbac_repository.py:1-213](file://service/src/infrastructure/repositories/rbac_repository.py#L1-L213)
- [dependencies.py:1-72](file://service/src/api/dependencies.py#L1-L72)
- [decorators.py:1-24](file://service/src/core/decorators.py#L1-L24)

## 性能考量
- 查询优化
  - 使用分页参数限制单页数量，避免一次性加载过多数据
  - 对角色/权限名称使用模糊查询时，建议配合索引与合理分页
- 关联查询
  - 用户权限查询通过 JOIN 一次性获取，减少 N+1 查询
  - 角色权限分配采用“清空-重建”，适合中低频变更场景
- 缓存策略（建议）
  - 用户权限集合可缓存于 Redis，键名建议包含 user_id 与版本号
  - 缓存过期时间可按权限变更频率设定，权限变更时主动失效
  - 菜单树可缓存，结合权限变更事件触发失效
- 日志与可观测性
  - 使用 log_execution 包裹热点函数，记录执行耗时与异常
  - 结合分布式追踪与指标埋点，定位慢查询与瓶颈

## 故障排查指南
- 权限不足
  - 现象：返回 403 Forbidden
  - 排查：确认用户是否为超级用户；核对用户权限编码集合是否包含所需权限
- 资源不存在
  - 现象：返回 404 Not Found
  - 排查：确认角色/权限/菜单 ID 是否正确；检查软删除与级联删除策略
- 冲突错误
  - 现象：返回 409 Conflict
  - 排查：角色/权限编码唯一性冲突；用户已分配角色冲突；菜单层级循环引用
- 鉴权失败
  - 现象：返回 401 Unauthorized
  - 排查：Token 过期或类型错误；用户被禁用或不存在

章节来源
- [dependencies.py:16-42](file://service/src/api/dependencies.py#L16-L42)
- [rbac_service.py:30-35](file://service/src/application/services/rbac_service.py#L30-L35)
- [rbac_repository.py:107-119](file://service/src/infrastructure/repositories/rbac_repository.py#L107-L119)
- [menu_service.py:82-94](file://service/src/application/services/menu_service.py#L82-L94)

## 结论
本 RBAC 子系统以清晰的分层架构实现了角色、权限、用户三者之间的灵活管理，具备完善的权限继承与动态校验能力。通过菜单权限关联与用户权限过滤，系统能够高效生成用户可见的菜单树。建议在生产环境中引入权限缓存与监控告警，持续优化查询与写入性能。

## 附录

### API 定义概览
- 角色管理
  - GET /api/system/role/list（分页）
  - POST /api/system/role/（新增）
  - GET /api/system/role/{role_id}（详情）
  - PUT /api/system/role/{role_id}（更新）
  - DELETE /api/system/role/{role_id}（删除）
- 权限管理
  - GET /api/system/permission/list（分页）
  - POST /api/system/permission/（新增）
  - DELETE /api/system/permission/{permission_id}（删除）
- 角色权限分配
  - POST /api/system/role/{role_id}/permissions（分配）
- 用户角色与权限
  - POST /api/system/user/{user_id}/roles（分配角色）
  - DELETE /api/system/user/{user_id}/roles/{role_id}（移除角色）
  - GET /api/system/user/{user_id}/roles（用户角色）
  - GET /api/system/user/{user_id}/permissions（用户权限）
  - GET /api/system/user/{user_id}/check-permission/{codename}（权限校验）

章节来源
- [rbac_routes.py:33-257](file://service/src/api/v1/rbac_routes.py#L33-L257)

### 最佳实践与安全考虑
- 最小权限原则：为角色分配必要的最小权限集合
- 审计与日志：记录权限变更与敏感操作，保留审计轨迹
- 输入校验：严格校验 DTO 字段长度与范围，避免注入与越界
- 超级用户管控：限制超级用户数量，定期复核
- 菜单权限一致性：菜单 permissions 字段与权限实体保持同步
- 缓存一致性：权限变更时主动失效相关缓存键