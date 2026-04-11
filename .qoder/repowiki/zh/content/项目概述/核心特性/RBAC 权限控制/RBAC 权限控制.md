# RBAC 权限控制

<cite>
**本文档引用的文件**
- [rbac_defaults.py](file://service/src/domain/rbac_defaults.py)
- [constants.py](file://service/src/api/constants.py)
- [models.py](file://service/src/infrastructure/database/models.py)
- [role_service.py](file://service/src/application/services/role_service.py)
- [permission_service.py](file://service/src/application/services/permission_service.py)
- [user_service.py](file://service/src/application/services/user_service.py)
- [role_routes.py](file://service/src/api/v1/role_routes.py)
- [permission_routes.py](file://service/src/api/v1/permission_routes.py)
- [menu_routes.py](file://service/src/api/v1/menu_routes.py)
- [dependencies.py](file://service/src/api/dependencies.py)
- [middlewares.py](file://service/src/infrastructure/http/middlewares.py)
- [redis_client.py](file://service/src/infrastructure/cache/redis_client.py)
- [auth.ts](file://web/src/utils/auth.ts)
- [index.ts](file://web/src/directives/perms/index.ts)
- [perms.tsx](file://web/src/components/RePerms/src/perms.tsx)
- [permission.ts](file://web/src/store/modules/permission.ts)
</cite>

## 更新摘要
**所做更改**
- 更新了默认权限定义的位置，从 `src/core/constants.py` 迁移到 `src/domain/rbac_defaults.py`
- 新增完整的默认权限定义，包含用户、角色、权限、菜单、部门、日志等各类权限
- 更新了相关服务和路由文件的引用路径
- 完善了权限系统的种子数据管理

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考虑](#性能考虑)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本文件面向 RBAC（基于角色的访问控制）权限控制系统，系统分为后端服务与前端界面两部分：
- 后端采用 FastAPI + SQLModel，提供角色、权限、用户三者关系的管理与校验；菜单权限与按钮权限由后端权限编码驱动，前端据此渲染与控制可见性。
- 前端采用 Vue 3 + TypeScript，通过指令与组件实现按钮级权限控制，通过权限状态管理与路由守卫实现菜单级权限过滤。

本技术文档将从数据模型、服务层、API 路由、中间件与前端集成等维度，系统阐述 RBAC 设计原理与实现细节，并给出最佳实践与性能优化建议。

## 项目结构
后端服务位于 service/src，前端界面位于 web/src。RBAC 相关的关键目录与文件如下：
- 后端
  - 数据模型：service/src/infrastructure/database/models.py
  - 仓储层：service/src/infrastructure/repositories/rbac_repository.py
  - 应用服务：service/src/application/services/rbac_service.py
  - API 路由：service/src/api/v1/rbac_routes.py、service/src/api/v1/menu_routes.py
  - DTO：service/src/application/dto/rbac_dto.py
  - 依赖注入与权限校验：service/src/api/dependencies.py
  - 中间件：service/src/infrastructure/http/middlewares.py
  - 缓存：service/src/infrastructure/cache/redis_client.py
  - 默认权限定义：service/src/domain/rbac_defaults.py
  - API 常量：service/src/api/constants.py
- 前端
  - 权限工具：web/src/utils/auth.ts
  - 指令 v-perms：web/src/directives/perms/index.ts
  - 组件 <Perms>：web/src/components/RePerms/src/perms.tsx
  - 权限状态管理：web/src/store/modules/permission.ts

```mermaid
graph TB
subgraph "后端"
A["FastAPI 应用<br/>API 路由"]
B["应用服务<br/>RoleService / PermissionService / UserService"]
C["仓储层<br/>RoleRepository / PermissionRepository"]
D["数据库模型<br/>Role / Permission / Menu / 关联表"]
E["依赖注入与权限校验<br/>require_permission()"]
F["中间件<br/>日志/请求耗时/IP黑白名单"]
G["缓存客户端<br/>Redis"]
H["默认权限定义<br/>rbac_defaults.py"]
I["API 常量<br/>constants.py"]
end
subgraph "前端"
J["权限工具<br/>auth.ts"]
K["指令 v-perms<br/>index.ts"]
L["组件 <Perms><br/>perms.tsx"]
M["权限状态管理<br/>permission.ts"]
end
A --> B --> C --> D
A --> E
A --> F
B --> G
H --> B
I --> A
J --> K
J --> L
J --> M
```

**图表来源**
- [role_routes.py:1-257](file://service/src/api/v1/role_routes.py#L1-L257)
- [permission_routes.py:1-71](file://service/src/api/v1/permission_routes.py#L1-L71)
- [menu_routes.py:1-71](file://service/src/api/v1/menu_routes.py#L1-L71)
- [dependencies.py:1-72](file://service/src/api/dependencies.py#L1-L72)
- [middlewares.py:1-65](file://service/src/infrastructure/http/middlewares.py#L1-L65)
- [redis_client.py:1-24](file://service/src/infrastructure/cache/redis_client.py#L1-L24)
- [rbac_defaults.py:1-37](file://service/src/domain/rbac_defaults.py#L1-L37)
- [constants.py:1-10](file://service/src/api/constants.py#L1-L10)
- [auth.ts:1-142](file://web/src/utils/auth.ts#L1-L142)
- [index.ts:1-16](file://web/src/directives/perms/index.ts#L1-L16)
- [perms.tsx:1-21](file://web/src/components/RePerms/src/perms.tsx#L1-L21)
- [permission.ts:1-76](file://web/src/store/modules/permission.ts#L1-L76)

**章节来源**
- [role_routes.py:1-257](file://service/src/api/v1/role_routes.py#L1-L257)
- [permission_routes.py:1-71](file://service/src/api/v1/permission_routes.py#L1-L71)
- [menu_routes.py:1-71](file://service/src/api/v1/menu_routes.py#L1-L71)
- [dependencies.py:1-72](file://service/src/api/dependencies.py#L1-L72)
- [middlewares.py:1-65](file://service/src/infrastructure/http/middlewares.py#L1-L65)
- [redis_client.py:1-24](file://service/src/infrastructure/cache/redis_client.py#L1-L24)
- [rbac_defaults.py:1-37](file://service/src/domain/rbac_defaults.py#L1-L37)
- [constants.py:1-10](file://service/src/api/constants.py#L1-L10)
- [auth.ts:1-142](file://web/src/utils/auth.ts#L1-L142)
- [index.ts:1-16](file://web/src/directives/perms/index.ts#L1-L16)
- [perms.tsx:1-21](file://web/src/components/RePerms/src/perms.tsx#L1-L21)
- [permission.ts:1-76](file://web/src/store/modules/permission.ts#L1-L76)

## 核心组件
- 数据模型与关系
  - 用户、角色、权限三者通过关联表建立多对多关系：用户-角色、角色-权限。
  - 菜单模型包含权限编码字符串，用于后端按权限过滤菜单。
- 默认权限定义
  - 新增完整的默认权限定义文件，包含用户管理、角色管理、权限管理、菜单管理、部门管理、日志管理等各类权限。
  - 默认角色包括管理员、普通用户、版主等预设角色。
- 仓储层
  - 提供角色、权限、用户-角色、角色-权限等 CRUD 与聚合查询。
  - 支持"先清后增"的权限分配策略，确保角色权限的原子替换。
- 应用服务
  - RoleService：封装角色管理业务逻辑。
  - PermissionService：封装权限管理业务逻辑。
  - UserService：封装用户管理业务逻辑，包含权限聚合计算。
- API 路由
  - 提供角色与权限的增删改查、权限分配、用户角色管理等接口。
  - 使用依赖项 require_permission 对接口进行动态权限校验。
- 前端
  - 权限工具：存储与解析用户权限，提供按钮级权限判断。
  - 指令与组件：v-perms 与 <Perms> 组件实现按钮级可见性控制。
  - 权限状态管理：整合菜单树与路由，过滤无权限节点。

**章节来源**
- [models.py:17-141](file://service/src/infrastructure/database/models.py#L17-L141)
- [rbac_defaults.py:3-37](file://service/src/domain/rbac_defaults.py#L3-L37)
- [role_service.py:11-174](file://service/src/application/services/role_service.py#L11-L174)
- [permission_service.py:11-62](file://service/src/application/services/permission_service.py#L11-L62)
- [user_service.py:24-319](file://service/src/application/services/user_service.py#L24-L319)
- [role_routes.py:30-257](file://service/src/api/v1/role_routes.py#L30-L257)
- [permission_routes.py:19-71](file://service/src/api/v1/permission_routes.py#L19-L71)
- [auth.ts:130-142](file://web/src/utils/auth.ts#L130-L142)
- [index.ts:4-16](file://web/src/directives/perms/index.ts#L4-L16)
- [perms.tsx:4-21](file://web/src/components/RePerms/src/perms.tsx#L4-L21)
- [permission.ts:25-71](file://web/src/store/modules/permission.ts#L25-L71)

## 架构总览
RBAC 架构遵循分层设计：API 路由层负责请求接入与权限依赖注入，应用服务层编排业务逻辑，仓储层封装数据访问，数据库模型定义实体与关系。前端通过指令与组件消费后端权限能力，实现菜单与按钮级权限控制。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant API as "API 路由"
participant Dep as "依赖注入<br/>require_permission()"
participant Svc as "应用服务<br/>RoleService/PermissionService/UserService"
participant Repo as "仓储层<br/>Role/Permission/User 仓储"
participant DB as "数据库"
Client->>API : "HTTP 请求"
API->>Dep : "校验用户与权限"
Dep->>Repo : "查询用户权限"
Repo->>DB : "执行查询"
DB-->>Repo : "权限集合"
Repo-->>Dep : "权限集合"
Dep-->>API : "通过/拒绝"
API->>Svc : "调用业务方法"
Svc->>Repo : "读写角色/权限/用户关系"
Repo->>DB : "执行 SQL"
DB-->>Repo : "结果"
Repo-->>Svc : "结果"
Svc-->>API : "业务结果"
API-->>Client : "响应"
```

**图表来源**
- [role_routes.py:33-177](file://service/src/api/v1/role_routes.py#L33-L177)
- [permission_routes.py:19-71](file://service/src/api/v1/permission_routes.py#L19-L71)
- [dependencies.py:45-61](file://service/src/api/dependencies.py#L45-L61)
- [role_service.py:19-231](file://service/src/application/services/role_service.py#L19-L231)
- [permission_service.py:24-62](file://service/src/application/services/permission_service.py#L24-L62)
- [user_service.py:272-319](file://service/src/application/services/user_service.py#L272-L319)

## 详细组件分析

### 数据模型与关系映射
- 实体与关系
  - User：用户实体，包含基础字段与状态。
  - Role：角色实体，包含唯一编码与状态。
  - Permission：权限实体，包含唯一编码、分类、资源与动作等。
  - 关联表：
    - RolePermissionLink：角色-权限多对多。
    - UserRole：用户-角色多对多。
  - Menu：菜单实体，包含权限编码字符串，用于后端按权限过滤。
- 复杂度与约束
  - 唯一索引：角色编码、权限编码唯一。
  - 外键级联：删除角色/用户时级联删除关联记录。
  - 查询复杂度：用户权限查询通过三层 JOIN，时间复杂度 O(n)（n 为用户角色数）。

```mermaid
erDiagram
USERS {
string id PK
string username UK
string email
string hashed_password
int status
bool is_superuser
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
string resource
string action
int status
}
ROLE_PERMISSION_LINK {
string role_id PK
string permission_id PK
}
USER_ROLES {
string id PK
string user_id
string role_id
}
MENUS {
string id PK
string name
string path
string component
string icon
string title
string parent_id
int order_num
string permissions
int status
}
USERS ||--o{ USER_ROLES : "拥有"
ROLES ||--o{ USER_ROLES : "被拥有"
ROLES ||--o{ ROLE_PERMISSION_LINK : "授予"
PERMISSIONS ||--o{ ROLE_PERMISSION_LINK : "被授予"
MENUS }o--|| MENUS : "父子关系"
```

**图表来源**
- [models.py:31-141](file://service/src/infrastructure/database/models.py#L31-L141)

**章节来源**
- [models.py:17-141](file://service/src/infrastructure/database/models.py#L17-L141)

### 默认权限定义与种子数据管理
- 默认权限定义位置迁移
  - 原位于 `src/core/constants.py` 的默认权限定义已迁移至 `src/domain/rbac_defaults.py`。
  - 新文件包含完整的默认角色和权限定义，提供系统初始化时的种子数据。
- 默认权限覆盖范围
  - 用户相关权限：查看用户、创建用户、编辑用户、删除用户
  - 角色相关权限：查看角色、管理角色
  - 权限相关权限：查看权限、管理权限
  - 菜单相关权限：查看菜单、创建菜单、编辑菜单、删除菜单
  - 部门相关权限：查看部门、创建部门、编辑部门、删除部门
  - 日志相关权限：查看登录日志、删除登录日志、查看操作日志、删除操作日志、查看系统日志、删除系统日志
- 默认角色定义
  - admin：系统管理员，拥有完全访问权限
  - user：普通用户，拥有基本访问权限
  - moderator：版主，拥有提升权限

```mermaid
flowchart TD
Start(["系统启动"]) --> LoadDefaults["加载默认权限定义<br/>rbac_defaults.py"]
LoadDefaults --> CreateRoles["创建默认角色<br/>admin, user, moderator"]
CreateRoles --> CreatePermissions["创建默认权限<br/>用户、角色、权限、菜单、部门、日志"]
CreatePermissions --> SeedComplete["种子数据完成"]
SeedComplete --> InitDB["初始化数据库"]
```

**图表来源**
- [rbac_defaults.py:3-37](file://service/src/domain/rbac_defaults.py#L3-L37)

**章节来源**
- [rbac_defaults.py:1-37](file://service/src/domain/rbac_defaults.py#L1-L37)

### 权限验证中间件与动态权限检查流程
- 动态权限依赖注入
  - require_permission(code) 依赖工厂：在路由层声明所需权限，运行时校验当前用户是否具备该权限编码。
  - 超级用户 bypass：is_superuser 为真时跳过权限校验。
- 校验流程
  - 从 JWT 解析用户 ID，校验令牌类型与有效性。
  - 通过 PermissionRepository 获取用户权限集合，匹配目标权限编码。
  - 未满足则抛出禁止访问错误，否则放行。
- 中间件
  - RequestLoggingMiddleware：统一记录请求与耗时。
  - IPFilterMiddleware：基于白/黑名单过滤访问。

```mermaid
flowchart TD
Start(["进入路由"]) --> GetUser["解析 JWT 获取用户ID"]
GetUser --> CheckToken{"令牌有效且类型正确？"}
CheckToken --> |否| Deny["抛出未授权错误"]
CheckToken --> |是| CheckSuper{"是否超级用户？"}
CheckSuper --> |是| Allow["放行"]
CheckSuper --> |否| LoadPerms["加载用户权限集合"]
LoadPerms --> Match{"是否包含所需权限编码？"}
Match --> |否| Deny
Match --> |是| Allow
```

**图表来源**
- [dependencies.py:45-61](file://service/src/api/dependencies.py#L45-L61)
- [middlewares.py:12-65](file://service/src/infrastructure/http/middlewares.py#L12-L65)

**章节来源**
- [dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)
- [middlewares.py:12-65](file://service/src/infrastructure/http/middlewares.py#L12-L65)

### 菜单权限生成与按钮权限控制
- 菜单权限生成
  - 后端菜单模型保存权限编码字符串，MenuService 在获取用户菜单时按权限集合过滤。
  - 超级用户返回全部菜单树；普通用户仅返回与用户权限有交集的菜单。
- 按钮权限控制
  - 前端权限工具 hasPerms 判断当前用户是否拥有指定按钮权限编码。
  - 指令 v-perms 与组件 <Perms> 在挂载时根据权限决定 DOM 是否渲染。
  - 权限状态管理整合菜单树与路由，过滤无权限节点。

```mermaid
sequenceDiagram
participant FE as "前端"
participant API as "菜单接口"
participant Svc as "MenuService"
participant Repo as "PermissionRepository"
participant DB as "数据库"
FE->>API : "获取用户菜单"
API->>Svc : "get_user_menus(user_id)"
Svc->>Repo : "get_user_permissions(user_id)"
Repo->>DB : "查询用户权限"
DB-->>Repo : "权限集合"
Repo-->>Svc : "权限集合"
Svc->>Svc : "按菜单权限编码过滤"
Svc-->>API : "菜单树"
API-->>FE : "返回菜单树"
FE->>FE : "指令/组件根据权限渲染"
```

**图表来源**
- [menu_routes.py:29-36](file://service/src/api/v1/menu_routes.py#L29-L36)
- [auth.ts:130-142](file://web/src/utils/auth.ts#L130-L142)
- [index.ts:4-16](file://web/src/directives/perms/index.ts#L4-L16)
- [perms.tsx:12-19](file://web/src/components/RePerms/src/perms.tsx#L12-L19)

**章节来源**
- [menu_routes.py:19-71](file://service/src/api/v1/menu_routes.py#L19-L71)
- [auth.ts:130-142](file://web/src/utils/auth.ts#L130-L142)
- [index.ts:4-16](file://web/src/directives/perms/index.ts#L4-L16)
- [perms.tsx:12-19](file://web/src/components/RePerms/src/perms.tsx#L12-L19)
- [permission.ts:25-34](file://web/src/store/modules/permission.ts#L25-L34)

### 角色、权限、用户关系与 API 工作流
- 角色与权限
  - 角色创建支持同时分配权限；更新角色可替换权限集合。
  - 为角色分配权限采用"先清后增"策略，保证幂等与一致性。
- 用户与角色/权限
  - 为用户分配角色时去重；移除角色时精确匹配。
  - 用户权限查询通过用户-角色-角色-权限链路聚合，去重返回。
- API 工作流
  - 角色管理与权限管理接口均通过 require_permission 进行动态校验。
  - 返回数据统一通过 DTO 转换，保持前后端契约稳定。

```mermaid
sequenceDiagram
participant Admin as "管理员"
participant RoleAPI as "角色接口"
participant PermAPI as "权限接口"
participant Svc as "RoleService/PermissionService"
participant Repo as "Role/Permission 仓储"
participant DB as "数据库"
Admin->>RoleAPI : "创建角色(可带权限)"
RoleAPI->>Svc : "create_role(dto)"
Svc->>Repo : "创建角色"
Repo->>DB : "插入角色"
DB-->>Repo : "角色ID"
Repo-->>Svc : "角色"
Svc->>Repo : "assign_permissions_to_role(role_id, ids)"
Repo->>DB : "先清后增"
DB-->>Repo : "成功"
Repo-->>Svc : "成功"
Svc-->>RoleAPI : "角色+权限"
RoleAPI-->>Admin : "返回角色详情"
Admin->>PermAPI : "创建权限"
PermAPI->>Svc : "create_permission(dto)"
Svc->>Repo : "创建权限"
Repo->>DB : "插入权限"
DB-->>Repo : "权限"
Repo-->>Svc : "权限"
Svc-->>PermAPI : "权限"
PermAPI-->>Admin : "返回权限"
```

**图表来源**
- [role_routes.py:64-177](file://service/src/api/v1/role_routes.py#L64-L177)
- [permission_routes.py:29-36](file://service/src/api/v1/permission_routes.py#L29-L36)
- [role_service.py:24-50](file://service/src/application/services/role_service.py#L24-L50)
- [permission_service.py:24-32](file://service/src/application/services/permission_service.py#L24-L32)

**章节来源**
- [role_routes.py:33-177](file://service/src/api/v1/role_routes.py#L33-L177)
- [permission_routes.py:19-71](file://service/src/api/v1/permission_routes.py#L19-L71)
- [role_service.py:24-147](file://service/src/application/services/role_service.py#L24-L147)
- [permission_service.py:24-62](file://service/src/application/services/permission_service.py#L24-L62)

## 依赖分析
- 组件耦合与内聚
  - API 路由依赖依赖注入与应用服务，职责清晰；应用服务依赖仓储接口，便于替换实现。
  - 仓储层依赖 SQLModel 与数据库模型，关注数据访问细节。
  - 前端权限工具与指令/组件解耦，通过权限状态管理统一消费。
  - 默认权限定义作为种子数据源，为系统初始化提供基础配置。
- 外部依赖
  - FastAPI、SQLModel、Pydantic、redis.asyncio。
- 循环依赖
  - 未发现循环导入；各层单向依赖，结构清晰。

```mermaid
graph LR
Routes["API 路由"] --> Services["应用服务"]
Services --> Repos["仓储层"]
Repos --> Models["数据库模型"]
Defaults["默认权限定义"] --> Services
FrontAuth["前端权限工具"] --> FrontDir["指令/组件"]
FrontDir --> FrontStore["权限状态管理"]
```

**图表来源**
- [role_routes.py:1-257](file://service/src/api/v1/role_routes.py#L1-L257)
- [permission_routes.py:1-71](file://service/src/api/v1/permission_routes.py#L1-L71)
- [menu_routes.py:1-71](file://service/src/api/v1/menu_routes.py#L1-L71)
- [role_service.py:1-174](file://service/src/application/services/role_service.py#L1-L174)
- [permission_service.py:1-62](file://service/src/application/services/permission_service.py#L1-L62)
- [user_service.py:1-319](file://service/src/application/services/user_service.py#L1-L319)
- [rbac_defaults.py:1-37](file://service/src/domain/rbac_defaults.py#L1-L37)
- [auth.ts:1-142](file://web/src/utils/auth.ts#L1-L142)
- [index.ts:1-16](file://web/src/directives/perms/index.ts#L1-L16)
- [perms.tsx:1-21](file://web/src/components/RePerms/src/perms.tsx#L1-L21)
- [permission.ts:1-76](file://web/src/store/modules/permission.ts#L1-L76)

**章节来源**
- [role_routes.py:1-257](file://service/src/api/v1/role_routes.py#L1-L257)
- [permission_routes.py:1-71](file://service/src/api/v1/permission_routes.py#L1-L71)
- [menu_routes.py:1-71](file://service/src/api/v1/menu_routes.py#L1-L71)
- [role_service.py:1-174](file://service/src/application/services/role_service.py#L1-L174)
- [permission_service.py:1-62](file://service/src/application/services/permission_service.py#L1-L62)
- [user_service.py:1-319](file://service/src/application/services/user_service.py#L1-L319)
- [rbac_defaults.py:1-37](file://service/src/domain/rbac_defaults.py#L1-L37)
- [auth.ts:1-142](file://web/src/utils/auth.ts#L1-L142)
- [index.ts:1-16](file://web/src/directives/perms/index.ts#L1-L16)
- [perms.tsx:1-21](file://web/src/components/RePerms/src/perms.tsx#L1-L21)
- [permission.ts:1-76](file://web/src/store/modules/permission.ts#L1-L76)

## 性能考虑
- 查询优化
  - 用户权限查询使用 JOIN 并去重，建议在权限编码与用户-角色关联上建立索引以提升匹配效率。
  - 菜单过滤采用集合交集，建议限制单个菜单关联权限数量，避免过多权限字符串导致匹配成本上升。
- 缓存策略
  - 可引入 Redis 缓存用户权限集合与菜单树，结合令牌失效时间进行缓存更新/淘汰。
  - 缓存客户端已提供连接管理，可在应用服务层封装缓存读写。
- 批量操作
  - 角色权限分配采用"先清后增"，在权限数量较大时建议批量插入以减少往返。
- 日志与监控
  - 使用请求耗时中间件记录慢查询与异常路径，结合指标监控定位热点接口。
- 默认权限加载
  - 系统启动时加载默认权限定义，建议在应用初始化阶段进行，避免重复加载。

**章节来源**
- [rbac_defaults.py:3-37](file://service/src/domain/rbac_defaults.py#L3-L37)
- [redis_client.py:10-24](file://service/src/infrastructure/cache/redis_client.py#L10-L24)
- [middlewares.py:12-39](file://service/src/infrastructure/http/middlewares.py#L12-L39)

## 故障排查指南
- 常见错误与定位
  - 未授权/权限不足：检查 require_permission 依赖是否正确声明，确认用户权限集合是否包含目标编码。
  - 用户不存在或账户禁用：检查 get_current_active_user 依赖与用户状态字段。
  - 角色/权限不存在：检查 DTO 校验与服务层异常抛出点。
  - 菜单删除失败：检查是否存在子菜单，避免破坏层级完整性。
  - 默认权限加载失败：检查 rbac_defaults.py 文件路径和格式。
- 建议排查步骤
  - 查看请求日志与耗时头，定位慢接口。
  - 校验 JWT 令牌类型与有效期，确认令牌解析正确。
  - 核对权限编码命名规范与大小写，避免匹配失败。
  - 前端检查权限状态管理与指令/组件使用方式。
  - 验证默认权限定义文件的完整性和正确性。

**章节来源**
- [dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)
- [role_routes.py:132-151](file://service/src/api/v1/role_routes.py#L132-L151)
- [permission_routes.py:117-129](file://service/src/api/v1/permission_routes.py#L117-L129)
- [rbac_defaults.py:1-37](file://service/src/domain/rbac_defaults.py#L1-L37)
- [middlewares.py:12-39](file://service/src/infrastructure/http/middlewares.py#L12-L39)

## 结论
本系统以清晰的分层架构实现了 RBAC 权限控制：后端通过依赖注入与应用服务实现动态权限校验与菜单/按钮级权限过滤，前端通过指令与组件实现 UI 层的权限控制。数据模型简洁明确，仓储层提供稳定的 CRUD 与聚合查询能力。默认权限定义文件的引入为系统提供了完整的种子数据支持。建议在生产环境中引入缓存与索引优化，并持续完善权限编码规范与前端权限状态管理。

## 附录
- 最佳实践
  - 权限编码命名规范：采用"资源:动作"语义，如 "menu:view"、"btn.add"。
  - 角色最小权限原则：为角色分配必要的最小权限集合。
  - 超级用户谨慎使用：仅在运维场景启用，避免滥用。
  - 前端权限控制：指令与组件双保险，避免仅依赖后端校验。
  - 默认权限管理：定期审查和更新默认权限定义，确保符合业务需求。
- 扩展性设计
  - 自定义权限类型：在 Permission 模型中新增字段（如资源、动作），在前端与后端分别扩展匹配逻辑。
  - 多租户支持：在用户、角色、权限模型中增加租户字段与过滤条件。
  - 权限继承：在角色层级上实现继承关系，扩展用户权限计算逻辑。
  - 动态权限定义：支持运行时添加新的权限类型和默认权限组合。
- 性能优化清单
  - 为权限编码与用户-角色关联建立索引。
  - 引入 Redis 缓存用户权限与菜单树。
  - 批量插入角色权限，减少数据库往返。
  - 使用异步查询与连接池，提升并发处理能力。
  - 优化默认权限加载机制，避免重复初始化。