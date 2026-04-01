# 领域层（Business Logic）

<cite>
**本文档引用的文件**
- [service/src/domain/services/password_service.py](file://service/src/domain/services/password_service.py)
- [service/src/domain/services/token_service.py](file://service/src/domain/services/token_service.py)
- [service/src/domain/entities/user.py](file://service/src/domain/entities/user.py)
- [service/src/domain/entities/role.py](file://service/src/domain/entities/role.py)
- [service/src/domain/entities/permission.py](file://service/src/domain/entities/permission.py)
- [service/src/domain/entities/menu.py](file://service/src/domain/entities/menu.py)
- [service/src/domain/entities/department.py](file://service/src/domain/entities/department.py)
- [service/src/domain/entities/log.py](file://service/src/domain/entities/log.py)
- [service/src/domain/repositories/user_repository.py](file://service/src/domain/repositories/user_repository.py)
- [service/src/domain/repositories/rbac_repository.py](file://service/src/domain/repositories/rbac_repository.py)
- [service/src/domain/repositories/menu_repository.py](file://service/src/domain/repositories/menu_repository.py)
- [service/src/domain/repositories/department_repository.py](file://service/src/domain/repositories/department_repository.py)
- [service/src/domain/repositories/log_repository.py](file://service/src/domain/repositories/log_repository.py)
- [service/src/application/services/auth_service.py](file://service/src/application/services/auth_service.py)
- [service/src/application/services/user_service.py](file://service/src/application/services/user_service.py)
- [service/src/application/dto/auth_dto.py](file://service/src/application/dto/auth_dto.py)
- [service/src/application/dto/user_dto.py](file://service/src/application/dto/user_dto.py)
- [service/src/infrastructure/repositories/user_repository.py](file://service/src/infrastructure/repositories/user_repository.py)
- [service/src/infrastructure/repositories/rbac_repository.py](file://service/src/infrastructure/repositories/rbac_repository.py)
- [service/src/infrastructure/repositories/menu_repository.py](file://service/src/infrastructure/repositories/menu_repository.py)
- [service/src/infrastructure/database/models.py](file://service/src/infrastructure/database/models.py)
- [service/src/config/settings.py](file://service/src/config/settings.py)
</cite>

## 目录
1. [引言](#引言)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖分析](#依赖分析)
7. [性能考虑](#性能考虑)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 引言
本文件聚焦 Hello-FastApi 的领域层（Business Logic），系统化阐述业务规则核心的设计与实现，包括：
- 领域对象建模与不变量维护
- 认证领域的密码服务与令牌服务
- 仓储接口的设计原则与抽象定义
- 领域服务的实现、业务规则验证与数据一致性保障
- 领域驱动设计（DDD）实践：聚合根、值对象、领域事件等
- 通过接口隔离提升领域逻辑独立性与可测试性

**重要更新**：领域服务已从应用层移动到领域层，密码服务和令牌服务现在是纯领域服务，不再依赖外部库，实现了更严格的领域驱动设计隔离。

## 项目结构
领域层位于 service/src/domain，采用"按特性分层 + 接口隔离"的组织方式：
- 认证领域：密码服务、令牌服务
- 实体层：用户、角色、权限、菜单、部门、日志等聚合根
- 仓储接口层：用户仓储、RBAC仓储、菜单仓储、部门仓储、日志仓储
- 应用层在 service/src/application 提供业务用例；基础设施层在 service/src/infrastructure 提供仓储的具体实现；数据库模型在 service/src/infrastructure/database/models.py。

```mermaid
graph TB
subgraph "领域层Domain"
PWS["PasswordService<br/>密码服务"]
TKS["TokenService<br/>令牌服务"]
UE["UserEntity<br/>用户实体"]
RE["RoleEntity<br/>角色实体"]
PE["PermissionEntity<br/>权限实体"]
ME["MenuEntity<br/>菜单实体"]
DE["DepartmentEntity<br/>部门实体"]
LE["LogEntity<br/>日志实体"]
URepoI["UserRepositoryInterface<br/>用户仓储接口"]
RRepoI["RoleRepositoryInterface<br/>角色仓储接口"]
PRRepoI["PermissionRepositoryInterface<br/>权限仓储接口"]
MRepoI["MenuRepositoryInterface<br/>菜单仓储接口"]
DRepoI["DepartmentRepositoryInterface<br/>部门仓储接口"]
LRepoI["LogRepositoryInterface<br/>日志仓储接口"]
end
subgraph "应用层Application"
AS["AuthService<br/>认证应用服务"]
US["UserService<br/>用户应用服务"]
ADTO["Auth DTO<br/>认证DTO"]
UDTO["User DTO<br/>用户DTO"]
end
subgraph "基础设施层Infrastructure"
URepo["UserRepository<br/>用户仓储实现"]
RRepo["RoleRepository / PermissionRepository<br/>RBAC仓储实现"]
MRepo["MenuRepository<br/>菜单仓储实现"]
Models["SQLModel 模型<br/>User/Role/Permission/Menu"]
Settings["Settings<br/>JWT/Redis/数据库配置"]
end
AS --> PWS
AS --> TKS
AS --> URepoI
AS --> RRepoI
AS --> PRRepoI
US --> PWS
US --> URepoI
AS --> ADTO
US --> UDTO
URepoI --> URepo
RRepoI --> RRepo
PRRepoI --> RRepo
MRepoI --> MRepo
DRepoI --> DRepo
LRepoI --> LRepo
URepo --> Models
RRepo --> Models
MRepo --> Models
AS --> Settings
US --> Settings
```

**图表来源**
- [service/src/domain/services/password_service.py:1-43](file://service/src/domain/services/password_service.py#L1-L43)
- [service/src/domain/services/token_service.py:1-93](file://service/src/domain/services/token_service.py#L1-L93)
- [service/src/domain/entities/user.py:1-200](file://service/src/domain/entities/user.py#L1-L200)
- [service/src/domain/entities/role.py:1-150](file://service/src/domain/entities/role.py#L1-L150)
- [service/src/domain/entities/permission.py:1-120](file://service/src/domain/entities/permission.py#L1-L120)
- [service/src/domain/entities/menu.py:1-180](file://service/src/domain/entities/menu.py#L1-L180)
- [service/src/domain/repositories/user_repository.py:1-50](file://service/src/domain/repositories/user_repository.py#L1-L50)
- [service/src/domain/repositories/rbac_repository.py:1-77](file://service/src/domain/repositories/rbac_repository.py#L1-L77)
- [service/src/domain/repositories/menu_repository.py:1-43](file://service/src/domain/repositories/menu_repository.py#L1-L43)

## 核心组件
- 密码服务 PasswordService：提供密码哈希与校验，封装加密细节，确保密码安全存储与验证。
- 令牌服务 TokenService：封装 JWT 的签发、刷新与解码，统一管理过期策略与算法。
- 实体层：UserEntity、RoleEntity、PermissionEntity、MenuEntity、DepartmentEntity、LogEntity 等聚合根，维护业务状态与不变量。
- 仓储接口层：UserRepositoryInterface、RoleRepositoryInterface、PermissionRepositoryInterface、MenuRepositoryInterface、DepartmentRepositoryInterface、LogRepositoryInterface 等，定义数据持久化的契约。
- 应用服务 AuthService / UserService：编排领域服务与仓储，执行业务规则与数据一致性保障。
- DTO：LoginDTO、RegisterDTO、LoginResponseDTO 等，承载输入输出的数据契约，配合 Pydantic 校验。

**章节来源**
- [service/src/domain/services/password_service.py:1-43](file://service/src/domain/services/password_service.py#L1-L43)
- [service/src/domain/services/token_service.py:1-93](file://service/src/domain/services/token_service.py#L1-L93)
- [service/src/domain/entities/user.py:1-200](file://service/src/domain/entities/user.py#L1-L200)
- [service/src/domain/repositories/user_repository.py:1-50](file://service/src/domain/repositories/user_repository.py#L1-L50)
- [service/src/application/services/auth_service.py:1-154](file://service/src/application/services/auth_service.py#L1-L154)

## 架构总览
领域层通过接口隔离与依赖倒置，将业务规则与基础设施解耦。应用服务持有仓储接口与领域服务，负责业务流程编排；基础设施层提供具体实现，面向 SQLModel ORM。

**重要更新**：领域服务现在位于领域层，实现了真正的领域驱动设计隔离，密码服务和令牌服务不再依赖外部库，通过构造函数注入配置参数。

```mermaid
classDiagram
class PasswordService {
+hash_password(password) str
+verify_password(plain, hashed) bool
}
class TokenService {
+create_access_token(data, expires_delta) str
+create_refresh_token(data, expires_delta) str
+decode_token(token) dict|None
+verify_token_type(payload, expected) bool
}
class UserEntity {
+id : str
+username : str
+email : str
+hashed_password : str
+is_active : bool
+created_at : datetime
+updated_at : datetime
}
class RoleEntity {
+id : str
+name : str
+code : str
+status : int
}
class PermissionEntity {
+id : str
+code : str
+name : str
+category : str
+resource : str
+action : str
+status : int
}
class UserRepositoryInterface {
<<interface>>
+get_by_id(user_id) UserEntity?
+get_by_username(username) UserEntity?
+get_by_email(email) UserEntity?
+get_all(skip, limit) UserEntity[]
+create(user) UserEntity
+update(user) UserEntity
+delete(user_id) bool
+count() int
}
class RoleRepositoryInterface {
<<interface>>
+get_by_id(role_id) RoleEntity?
+get_by_name(name) RoleEntity?
+get_by_code(code) RoleEntity?
+get_all(page_num, page_size, ...) RoleEntity[]
+count(...) int
+create(role) RoleEntity
+update(role) RoleEntity
+delete(role_id) bool
+assign_permissions_to_role(role_id, perm_ids) bool
+get_role_permissions(role_id) PermissionEntity[]
+assign_role_to_user(user_id, role_id) bool
+remove_role_from_user(user_id, role_id) bool
+get_user_roles(user_id) RoleEntity[]
}
class PermissionRepositoryInterface {
<<interface>>
+get_by_id(permission_id) PermissionEntity?
+get_by_code(code) PermissionEntity?
+get_all(page_num, page_size, ...) PermissionEntity[]
+count(...) int
+create(permission) PermissionEntity
+delete(permission_id) bool
+get_permissions_by_role(role_id) PermissionEntity[]
+get_user_permissions(user_id) PermissionEntity[]
}
class MenuRepositoryInterface {
<<interface>>
+get_all(session) MenuEntity[]
+get_by_id(menu_id, session) MenuEntity?
+create(menu, session) MenuEntity
+update(menu, session) MenuEntity
+delete(menu_id, session) bool
+get_by_parent_id(parent_id, session) MenuEntity[]
}
class AuthService {
-session
-user_repo
-role_repo
-perm_repo
-token_service
-password_service
+login(dto) dict
+register(dto) dict
+refresh_token(refresh_token) dict
}
class UserService {
-repo
-password_service
+create_user(dto) UserResponseDTO
+get_user(user_id) UserResponseDTO
+get_users(query) (UserResponseDTO[], int)
+update_user(user_id, dto) UserResponseDTO
+delete_user(user_id) bool
+batch_delete_users(ids) dict
+reset_password(user_id, new_password) bool
+update_status(user_id, status) bool
+change_password(user_id, dto) bool
+create_superuser(dto) UserResponseDTO
}
AuthService --> PasswordService : "使用"
AuthService --> TokenService : "使用"
AuthService --> UserRepositoryInterface : "依赖"
AuthService --> RoleRepositoryInterface : "依赖"
AuthService --> PermissionRepositoryInterface : "依赖"
UserService --> PasswordService : "使用"
UserService --> UserRepositoryInterface : "依赖"
```

**图表来源**
- [service/src/domain/services/password_service.py:10-43](file://service/src/domain/services/password_service.py#L10-L43)
- [service/src/domain/services/token_service.py:13-93](file://service/src/domain/services/token_service.py#L13-L93)
- [service/src/domain/entities/user.py:1-200](file://service/src/domain/entities/user.py#L1-L200)
- [service/src/domain/repositories/user_repository.py:1-50](file://service/src/domain/repositories/user_repository.py#L1-L50)
- [service/src/application/services/auth_service.py:1-154](file://service/src/application/services/auth_service.py#L1-L154)

## 详细组件分析

### 认证领域：密码服务与令牌服务
**重要更新**：密码服务和令牌服务现在位于领域层，是纯领域服务，不再依赖外部库。

- 密码服务 PasswordService
  - 哈希策略：使用 bcrypt 对明文密码进行哈希，确保不可逆与抗彩虹表。
  - 校验策略：比较明文与存储哈希值，返回布尔结果。
  - 不变性：哈希过程与盐生成由服务内部完成，调用方仅传入明文。
- 令牌服务 TokenService
  - 访问令牌：携带 exp 与 type=access，使用构造函数注入的密钥与算法签名。
  - 刷新令牌：携带 exp 与 type=refresh，独立有效期策略。
  - 解码与校验：统一捕获 JWTError 并返回 None，避免异常泄露。
  - 类型校验：通过 payload.type 校验令牌用途，防止误用。
  - **纯领域服务**：通过构造函数注入配置参数，不直接依赖配置模块，实现与配置层的解耦。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant AuthSvc as "AuthService"
participant UserRepo as "UserRepository"
participant PWS as "PasswordService"
participant TKS as "TokenService"
participant RoleRepo as "RoleRepository"
participant PermRepo as "PermissionRepository"
Client->>AuthSvc : "POST 登录"
AuthSvc->>UserRepo : "按用户名查询"
UserRepo-->>AuthSvc : "返回用户或空"
AuthSvc->>PWS : "校验密码"
PWS-->>AuthSvc : "匹配/不匹配"
AuthSvc->>TKS : "创建访问/刷新令牌"
TKS-->>AuthSvc : "返回令牌"
AuthSvc->>RoleRepo : "查询用户角色"
RoleRepo-->>AuthSvc : "返回角色列表"
AuthSvc->>PermRepo : "查询用户权限"
PermRepo-->>AuthSvc : "返回权限列表"
AuthSvc-->>Client : "返回登录响应"
```

**图表来源**
- [service/src/application/services/auth_service.py:26-74](file://service/src/application/services/auth_service.py#L26-L74)
- [service/src/domain/services/password_service.py:16-43](file://service/src/domain/services/password_service.py#L16-L43)
- [service/src/domain/services/token_service.py:20-93](file://service/src/domain/services/token_service.py#L20-L93)

**章节来源**
- [service/src/domain/services/password_service.py:1-43](file://service/src/domain/services/password_service.py#L1-L43)
- [service/src/domain/services/token_service.py:1-93](file://service/src/domain/services/token_service.py#L1-L93)
- [service/src/application/services/auth_service.py:26-74](file://service/src/application/services/auth_service.py#L26-L74)

### 实体层：领域对象建模
**重要更新**：实体层现在包含完整的聚合根定义，包括用户、角色、权限、菜单、部门、日志等。

- 用户实体 UserEntity
  - 维护用户的基本信息、认证凭据和状态
  - 包含用户名、邮箱、哈希密码、激活状态等字段
- 角色实体 RoleEntity
  - 维护角色的标识信息和状态
  - 包含名称、编码、状态等字段
- 权限实体 PermissionEntity
  - 维护权限的细粒度控制信息
  - 包含资源、操作、分类等字段
- 菜单实体 MenuEntity
  - 维护菜单树形结构和层级关系
  - 支持父子关系查询和排序
- 部门实体 DepartmentEntity
  - 维护组织架构信息
- 日志实体 LoginLogEntity、OperationLogEntity、SystemLogEntity
  - 维护各类系统日志信息

**章节来源**
- [service/src/domain/entities/user.py:1-200](file://service/src/domain/entities/user.py#L1-L200)
- [service/src/domain/entities/role.py:1-150](file://service/src/domain/entities/role.py#L1-L150)
- [service/src/domain/entities/permission.py:1-120](file://service/src/domain/entities/permission.py#L1-L120)
- [service/src/domain/entities/menu.py:1-180](file://service/src/domain/entities/menu.py#L1-L180)

### 仓储接口层：抽象定义
**重要更新**：仓储接口层现在包含完整的接口定义，涵盖用户、RBAC、菜单、部门、日志等所有领域。

- 用户仓储接口 UserRepositoryInterface
  - 定义用户唯一性查询（用户名/邮箱）、分页查询、创建/更新/删除、计数等。
  - 通过抽象方法约束实现，确保业务规则在应用层统一执行。
- RBAC 仓储接口 RoleRepositoryInterface / PermissionRepositoryInterface
  - 支持角色与权限的增删改查、分配与查询关系的能力。
  - 提供角色-权限分配、角色-用户分配与查询。
- 菜单仓储接口 MenuRepositoryInterface
  - 定义菜单树形结构与层级查询能力。
- 部门仓储接口 DepartmentRepositoryInterface
  - 定义部门的 CRUD 操作和层级查询。
- 日志仓储接口 LogRepositoryInterface
  - 定义各类日志的查询和管理能力。

**章节来源**
- [service/src/domain/repositories/user_repository.py:1-50](file://service/src/domain/repositories/user_repository.py#L1-L50)
- [service/src/domain/repositories/rbac_repository.py:1-77](file://service/src/domain/repositories/rbac_repository.py#L1-L77)
- [service/src/domain/repositories/menu_repository.py:1-43](file://service/src/domain/repositories/menu_repository.py#L1-L43)

### 用户领域：仓储接口与应用服务
- 用户应用服务 UserService
  - 创建用户：校验唯一性（用户名/邮箱），哈希密码，持久化并返回响应 DTO。
  - 更新用户：选择性更新，再次校验邮箱唯一性。
  - 修改密码：校验旧密码，哈希新密码后更新。
  - 重置密码：管理员重置，直接哈希并写入。
  - 批量删除：统计删除数量，返回结果。
  - 状态变更：启用/禁用用户。
  - 内部查询：按用户名获取用户实体，供其他服务复用。

```mermaid
flowchart TD
Start(["进入创建用户"]) --> CheckU["检查用户名唯一性"]
CheckU --> UOK{"唯一？"}
UOK -- "否" --> RaiseConflict["抛出冲突错误"]
UOK -- "是" --> CheckE["检查邮箱唯一性"]
CheckE --> EOK{"唯一？"}
EOK -- "否" --> RaiseConflict
EOK -- "是" --> HashPwd["密码哈希"]
HashPwd --> BuildEntity["构建用户实体"]
BuildEntity --> Persist["持久化保存"]
Persist --> ToResp["转换为响应DTO"]
ToResp --> End(["返回"])
RaiseConflict --> End
```

**图表来源**
- [service/src/application/services/user_service.py:25-57](file://service/src/application/services/user_service.py#L25-L57)
- [service/src/application/dto/user_dto.py:8-19](file://service/src/application/dto/user_dto.py#L8-L19)
- [service/src/domain/services/password_service.py:16-43](file://service/src/domain/services/password_service.py#L16-L43)

**章节来源**
- [service/src/application/services/user_service.py:25-57](file://service/src/application/services/user_service.py#L25-L57)
- [service/src/application/dto/user_dto.py:8-19](file://service/src/application/dto/user_dto.py#L8-L19)

### RBAC 领域：角色与权限仓储
- 角色仓储接口 RoleRepositoryInterface
  - 支持按名称/编码/ID 查询，分页与计数。
  - 提供角色-权限分配、角色-用户分配与查询。
- 权限仓储接口 PermissionRepositoryInterface
  - 支持按编码/ID 查询，分页与计数。
  - 提供角色权限与用户权限查询。
- 基础设施实现
  - RoleRepository：基于多对多关联表 RolePermissionLink 与 UserRole，实现分配/查询。
  - PermissionRepository：实现权限与角色/用户的关联查询。

```mermaid
erDiagram
ROLE {
string id PK
string name
string code UK
int status
}
PERMISSION {
string id PK
string code UK
string name
string category
string resource
string action
int status
}
ROLE_PERMISSION_LINK {
string role_id PK,FK
string permission_id PK,FK
}
USER_ROLE {
string id PK
string user_id FK
string role_id FK
}
ROLE ||--o{ USER_ROLE : "拥有"
ROLE ||--o{ ROLE_PERMISSION_LINK : "授予"
PERMISSION ||--o{ ROLE_PERMISSION_LINK : "被授予"
```

**图表来源**
- [service/src/infrastructure/database/models.py:17-141](file://service/src/infrastructure/database/models.py#L17-L141)
- [service/src/domain/repositories/rbac_repository.py:8-77](file://service/src/domain/repositories/rbac_repository.py#L8-L77)
- [service/src/infrastructure/repositories/rbac_repository.py:11-213](file://service/src/infrastructure/repositories/rbac_repository.py#L11-L213)

**章节来源**
- [service/src/domain/repositories/rbac_repository.py:1-77](file://service/src/domain/repositories/rbac_repository.py#L1-L77)
- [service/src/infrastructure/repositories/rbac_repository.py:1-213](file://service/src/infrastructure/repositories/rbac_repository.py#L1-L213)
- [service/src/infrastructure/database/models.py:17-141](file://service/src/infrastructure/database/models.py#L17-L141)

### 菜单领域：仓储接口
- 菜单仓储接口 MenuRepositoryInterface
  - 支持获取全部、按 ID 查询、按父 ID 查询子菜单、创建/更新/删除。
- 基础设施实现 MenuRepository
  - 使用 SQLModel 查询，按排序号排序，支持父子关系查询。

**章节来源**
- [service/src/domain/repositories/menu_repository.py:1-43](file://service/src/domain/repositories/menu_repository.py#L1-L43)
- [service/src/infrastructure/repositories/menu_repository.py:1-50](file://service/src/infrastructure/repositories/menu_repository.py#L1-L50)
- [service/src/infrastructure/database/models.py:146-171](file://service/src/infrastructure/database/models.py#L146-L171)

### 领域建模最佳实践与 DDD 实践
**重要更新**：领域层现在完全符合 DDD 原则，实现了真正的领域驱动设计隔离。

- 聚合根与实体
  - UserEntity/RoleEntity/PermissionEntity/MenuEntity 为聚合根，各自维护状态与行为（如 UserEntity 的 is_active）。
- 值对象
  - DTO（如 LoginDTO、UserCreateDTO）作为值对象，承载输入/输出数据契约，避免副作用。
- 领域服务
  - PasswordService/TokenService 封装跨聚合的业务能力，避免在应用服务中散落加密与令牌逻辑。
  - **纯领域服务**：通过构造函数注入配置参数，不依赖外部库，实现与配置层的解耦。
- 领域事件
  - 当前未见显式领域事件发布；可在用户状态变更、角色分配等关键动作处引入事件，以支持审计与异步处理。

**章节来源**
- [service/src/domain/entities/user.py:1-200](file://service/src/domain/entities/user.py#L1-L200)
- [service/src/application/dto/auth_dto.py:7-54](file://service/src/application/dto/auth_dto.py#L7-L54)
- [service/src/application/dto/user_dto.py:8-86](file://service/src/application/dto/user_dto.py#L8-L86)

## 依赖分析
**重要更新**：依赖关系现在更加清晰，领域服务位于领域层，实现了严格的依赖倒置。

- 应用服务依赖领域服务与仓储接口，不直接依赖具体实现，满足依赖倒置。
- 领域服务现在位于领域层，密码服务和令牌服务是纯领域服务，不再依赖外部库。
- 基础设施仓储实现依赖领域接口，向上提供一致的业务能力。
- 配置模块集中管理 JWT 密钥、算法与过期时间，通过构造函数注入到令牌服务。

```mermaid
graph LR
AS["AuthService"] --> PWS["PasswordService"]
AS --> TKS["TokenService"]
AS --> URepoI["UserRepositoryInterface"]
AS --> RRepoI["RoleRepositoryInterface"]
AS --> PRRepoI["PermissionRepositoryInterface"]
US["UserService"] --> PWS
US --> URepoI
URepoI --> URepo["UserRepository"]
RRepoI --> RRepo["RoleRepository/PermissionRepository"]
PRRepoI --> RRepo
MRepoI --> MRepo["MenuRepository"]
TKS --> Settings["Settings(JWT配置)"]
AS --> Settings
US --> Settings
```

**图表来源**
- [service/src/application/services/auth_service.py:18-24](file://service/src/application/services/auth_service.py#L18-L24)
- [service/src/application/services/user_service.py:21-23](file://service/src/application/services/user_service.py#L21-L23)
- [service/src/domain/services/token_service.py:20-33](file://service/src/domain/services/token_service.py#L20-L33)
- [service/src/config/settings.py:63-67](file://service/src/config/settings.py#L63-L67)

**章节来源**
- [service/src/application/services/auth_service.py:1-154](file://service/src/application/services/auth_service.py#L1-L154)
- [service/src/application/services/user_service.py:1-322](file://service/src/application/services/user_service.py#L1-L322)
- [service/src/config/settings.py:1-198](file://service/src/config/settings.py#L1-L198)

## 性能考虑
- 查询优化
  - 用户/角色/权限仓储均支持筛选与分页，建议在高频查询上增加索引（如用户名、邮箱、角色编码、权限编码）。
- 缓存策略
  - 可结合 Redis 缓存热点用户信息与权限集合，降低数据库压力。
- 事务边界
  - 应用服务中涉及多表写入（如创建用户并分配默认角色）应置于同一事务，确保一致性。
- 密码哈希成本
  - bcrypt 默认成本较高，注意在高并发场景下的延迟与资源占用，必要时调整成本参数。
- **领域服务性能**
  - 密码服务和令牌服务作为纯领域服务，性能开销主要来自 bcrypt 和 JWT 操作，建议合理配置成本参数和缓存策略。

## 故障排查指南
- 认证失败
  - 用户名或密码错误：检查密码哈希与校验流程，确认 DTO 字段与仓储查询。
  - 用户被禁用：确认状态字段与业务规则。
- 令牌问题
  - 无效刷新令牌：检查解码与类型校验，确认用户状态。
  - JWT 算法或密钥不匹配：核对配置项与服务端签名算法。
  - **领域服务配置问题**：检查令牌服务的构造函数参数配置。
- 用户唯一性冲突
  - 注册/更新时邮箱或用户名冲突：检查仓储唯一性查询与 DTO 校验。
- 权限/角色分配异常
  - 分配前清空旧关联再插入新关联，确保幂等性；检查外键与级联删除策略。

**章节来源**
- [service/src/application/services/auth_service.py:40-48](file://service/src/application/services/auth_service.py#L40-L48)
- [service/src/application/services/auth_service.py:130-143](file://service/src/application/services/auth_service.py#L130-L143)
- [service/src/application/services/user_service.py:38-41](file://service/src/application/services/user_service.py#L38-L41)
- [service/src/infrastructure/repositories/rbac_repository.py:84-96](file://service/src/infrastructure/repositories/rbac_repository.py#L84-L96)

## 结论
领域层通过清晰的接口划分与稳定的业务规则封装，实现了与基础设施的解耦与可测试性。**重要更新**：领域服务已移动到领域层，密码服务和令牌服务现在是纯领域服务，不再依赖外部库，实现了更严格的领域驱动设计隔离。认证领域的密码与令牌服务、用户与 RBAC 的仓储接口、以及应用服务的流程编排共同构成了稳定可靠的业务内核。建议在后续迭代中引入领域事件与缓存策略，进一步增强可观测性与性能表现。

## 附录
- 配置要点
  - JWT 密钥、算法与过期时间在配置模块集中管理，通过构造函数注入到令牌服务。
- 数据模型要点
  - 用户/角色/权限/菜单模型定义了完整的多对多关系与外键约束，支撑 RBAC 与菜单树形结构。
- **领域层结构**
  - 领域层现在包含完整的实体、仓储接口和服务层，实现了真正的 DDD 隔离。

**章节来源**
- [service/src/config/settings.py:63-67](file://service/src/config/settings.py#L63-L67)
- [service/src/domain/services/token_service.py:20-33](file://service/src/domain/services/token_service.py#L20-L33)
- [service/src/infrastructure/database/models.py:17-171](file://service/src/infrastructure/database/models.py#L17-L171)