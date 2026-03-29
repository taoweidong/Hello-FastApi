# 表现层（API Routes）

<cite>
**本文引用的文件**
- [service/src/api/v1/__init__.py](file://service/src/api/v1/__init__.py)
- [service/src/api/v1/auth_routes.py](file://service/src/api/v1/auth_routes.py)
- [service/src/api/v1/user_routes.py](file://service/src/api/v1/user_routes.py)
- [service/src/api/v1/rbac_routes.py](file://service/src/api/v1/rbac_routes.py)
- [service/src/api/v1/menu_routes.py](file://service/src/api/v1/menu_routes.py)
- [service/src/api/dependencies.py](file://service/src/api/dependencies.py)
- [service/src/api/common.py](file://service/src/api/common.py)
- [service/src/main.py](file://service/src/main.py)
- [service/src/application/dto/auth_dto.py](file://service/src/application/dto/auth_dto.py)
- [service/src/application/dto/user_dto.py](file://service/src/application/dto/user_dto.py)
- [service/src/application/dto/rbac_dto.py](file://service/src/application/dto/rbac_dto.py)
- [service/src/application/dto/menu_dto.py](file://service/src/application/dto/menu_dto.py)
- [service/src/core/constants.py](file://service/src/core/constants.py)
- [service/src/config/settings.py](file://service/src/config/settings.py)
- [service/src/core/middlewares.py](file://service/src/core/middlewares.py)
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
本文件聚焦 Hello-FastApi 的表现层（API Routes），系统性阐述 FastAPI 路由组织、请求处理流程与响应格式标准化。v1 版本路由模块以“系统路由聚合器”为核心，按领域拆分为认证、用户、RBAC（角色-权限）、菜单四大子路由，并通过统一的依赖注入体系实现权限校验与用户身份获取。同时，文档覆盖中间件集成、全局异常处理、API 版本管理与最佳实践，帮助开发者快速理解并扩展路由层。

## 项目结构
- 路由聚合与版本前缀
  - v1 路由聚合器将认证、用户、角色、权限、菜单路由统一挂载至系统前缀，形成清晰的 API 结构。
  - 系统前缀由常量定义，最终在应用工厂中作为路由前缀注册。
- 路由模块划分
  - 认证路由：登录、注册、登出、刷新令牌。
  - 用户路由：列表、创建、详情、更新、删除、批量删除、重置密码、状态变更、当前用户信息、密码修改。
  - RBAC 路由：角色列表、创建、详情、更新、删除、为角色分配权限；权限列表、创建、删除。
  - 菜单路由：菜单树、用户可见菜单、创建、更新、删除。
- 依赖与公共组件
  - 依赖项：基于 HTTP Bearer Token 的用户身份解析、活跃用户校验、权限校验、超级用户校验。
  - 公共组件：统一响应体、分页响应体、错误响应体与辅助函数。

```mermaid
graph TB
A["应用工厂<br/>service/src/main.py"] --> B["系统路由聚合器<br/>service/src/api/v1/__init__.py"]
B --> C["认证路由<br/>service/src/api/v1/auth_routes.py"]
B --> D["用户路由<br/>service/src/api/v1/user_routes.py"]
B --> E["RBAC 路由<br/>service/src/api/v1/rbac_routes.py"]
B --> F["菜单路由<br/>service/src/api/v1/menu_routes.py"]
A --> G["中间件<br/>service/src/core/middlewares.py"]
A --> H["配置<br/>service/src/config/settings.py"]
A --> I["常量<br/>service/src/core/constants.py"]
C --> J["依赖项<br/>service/src/api/dependencies.py"]
D --> J
E --> J
F --> J
C --> K["DTO<br/>service/src/application/dto/auth_dto.py"]
D --> L["DTO<br/>service/src/application/dto/user_dto.py"]
E --> M["DTO<br/>service/src/application/dto/rbac_dto.py"]
F --> N["DTO<br/>service/src/application/dto/menu_dto.py"]
C --> O["公共响应<br/>service/src/api/common.py"]
D --> O
E --> O
F --> O
```

图表来源
- [service/src/main.py:34-96](file://service/src/main.py#L34-L96)
- [service/src/api/v1/__init__.py:13-40](file://service/src/api/v1/__init__.py#L13-L40)
- [service/src/api/v1/auth_routes.py:16-86](file://service/src/api/v1/auth_routes.py#L16-L86)
- [service/src/api/v1/user_routes.py:24-252](file://service/src/api/v1/user_routes.py#L24-L252)
- [service/src/api/v1/rbac_routes.py:30-257](file://service/src/api/v1/rbac_routes.py#L30-L257)
- [service/src/api/v1/menu_routes.py:15-71](file://service/src/api/v1/menu_routes.py#L15-L71)
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)
- [service/src/api/common.py:29-65](file://service/src/api/common.py#L29-L65)
- [service/src/application/dto/auth_dto.py:7-54](file://service/src/application/dto/auth_dto.py#L7-L54)
- [service/src/application/dto/user_dto.py:8-86](file://service/src/application/dto/user_dto.py#L8-L86)
- [service/src/application/dto/rbac_dto.py:8-88](file://service/src/application/dto/rbac_dto.py#L8-L88)
- [service/src/application/dto/menu_dto.py:8-56](file://service/src/application/dto/menu_dto.py#L8-L56)
- [service/src/core/constants.py:4-6](file://service/src/core/constants.py#L4-L6)
- [service/src/config/settings.py:47-51](file://service/src/config/settings.py#L47-L51)

章节来源
- [service/src/api/v1/__init__.py:13-40](file://service/src/api/v1/__init__.py#L13-L40)
- [service/src/core/constants.py:4-6](file://service/src/core/constants.py#L4-L6)
- [service/src/config/settings.py:47-51](file://service/src/config/settings.py#L47-L51)

## 核心组件
- 系统路由聚合器
  - 将认证、用户、角色、权限、菜单路由按前缀挂载，统一标签分类，便于文档生成与维护。
- 依赖注入体系
  - HTTP Bearer 令牌解析与校验、当前活跃用户获取、权限校验（支持超级用户豁免）、超级用户校验。
- 统一响应与分页
  - 统一响应体包含 code、message、data；分页响应体包含 total、pageNum、pageSize、totalPage、rows。
- DTO 层
  - 认证、用户、RBAC、菜单各领域 DTO 定义，确保请求/响应结构清晰且具备字段约束。

章节来源
- [service/src/api/v1/__init__.py:13-40](file://service/src/api/v1/__init__.py#L13-L40)
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)
- [service/src/api/common.py:29-65](file://service/src/api/common.py#L29-L65)
- [service/src/application/dto/auth_dto.py:7-54](file://service/src/application/dto/auth_dto.py#L7-L54)
- [service/src/application/dto/user_dto.py:8-86](file://service/src/application/dto/user_dto.py#L8-L86)
- [service/src/application/dto/rbac_dto.py:8-88](file://service/src/application/dto/rbac_dto.py#L8-L88)
- [service/src/application/dto/menu_dto.py:8-56](file://service/src/application/dto/menu_dto.py#L8-L56)

## 架构总览
- 应用启动与路由注册
  - 应用工厂创建 FastAPI 实例，配置文档路径、CORS、请求日志中间件、全局异常处理器，并在 lifespan 中初始化/关闭数据库。
  - 将系统路由聚合器以系统前缀注册到应用。
- 请求处理链路
  - 中间件 → 路由装饰器 → 依赖注入（权限/用户）→ 业务服务 → 统一响应封装。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant App as "FastAPI 应用<br/>service/src/main.py"
participant MW as "中间件<br/>service/src/core/middlewares.py"
participant Router as "路由处理器<br/>v1 子模块"
participant Dep as "依赖注入<br/>service/src/api/dependencies.py"
participant Svc as "业务服务<br/>application/services/*"
participant Resp as "统一响应<br/>service/src/api/common.py"
Client->>App : "HTTP 请求"
App->>MW : "进入中间件链"
MW-->>App : "请求日志/处理时间"
App->>Router : "匹配路由装饰器"
Router->>Dep : "执行依赖令牌解码/权限校验"
Dep-->>Router : "返回用户/权限上下文"
Router->>Svc : "调用业务服务"
Svc-->>Router : "返回业务结果"
Router->>Resp : "封装统一响应"
Resp-->>Client : "JSON 响应"
```

图表来源
- [service/src/main.py:34-96](file://service/src/main.py#L34-L96)
- [service/src/core/middlewares.py:12-39](file://service/src/core/middlewares.py#L12-L39)
- [service/src/api/v1/auth_routes.py:19-86](file://service/src/api/v1/auth_routes.py#L19-L86)
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)
- [service/src/api/common.py:45-65](file://service/src/api/common.py#L45-L65)

## 详细组件分析

### 认证路由（auth_routes）
- 路由装饰器与请求处理
  - 登录：接收登录 DTO，调用认证服务登录，返回统一响应。
  - 注册：接收注册 DTO，调用认证服务注册，返回统一响应。
  - 刷新：接收刷新令牌 DTO，调用认证服务刷新，返回统一响应。
  - 登出：依赖当前活跃用户，返回统一响应（JWT 无状态，服务端不存储）。
- 依赖注入
  - 使用数据库会话依赖与统一的认证服务。
- 响应格式
  - 统一响应体，包含 code、message、data。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant Auth as "认证路由<br/>service/src/api/v1/auth_routes.py"
participant Dep as "依赖注入<br/>service/src/api/dependencies.py"
participant Svc as "AuthService<br/>application/services/auth_service.py"
participant Resp as "统一响应<br/>service/src/api/common.py"
Client->>Auth : "POST /api/system/login"
Auth->>Dep : "get_db()"
Auth->>Svc : "login(LoginDTO)"
Svc-->>Auth : "登录结果"
Auth->>Resp : "success_response(...)"
Resp-->>Client : "{code,message,data}"
```

图表来源
- [service/src/api/v1/auth_routes.py:19-86](file://service/src/api/v1/auth_routes.py#L19-L86)
- [service/src/api/dependencies.py:16-39](file://service/src/api/dependencies.py#L16-L39)
- [service/src/api/common.py:45-47](file://service/src/api/common.py#L45-L47)

章节来源
- [service/src/api/v1/auth_routes.py:19-86](file://service/src/api/v1/auth_routes.py#L19-L86)
- [service/src/application/dto/auth_dto.py:7-54](file://service/src/application/dto/auth_dto.py#L7-L54)

### 用户路由（user_routes）
- 功能覆盖
  - 列表（分页+筛选）、创建、详情、更新、删除、批量删除、重置密码、状态变更、当前用户信息、密码修改。
- 权限控制
  - 大多数写操作依赖 require_permission 工厂生成的依赖，确保最小权限原则。
- 请求参数处理
  - 查询参数使用 Pydantic DTO，如用户列表查询 DTO；路径参数使用 str 类型。
- 响应格式
  - 列表使用分页响应；其他操作使用统一响应。

```mermaid
flowchart TD
Start(["进入用户路由"]) --> Op{"操作类型？"}
Op --> |列表| Q["解析查询DTO<br/>UserListQueryDTO"]
Q --> P["require_permission('user:view')"]
P --> S["UserService.get_users()"]
S --> R1["page_response(...)"]
Op --> |创建| C["require_permission('user:add')"]
C --> S2["UserService.create_user()"]
S2 --> R2["success_response(..., code=201)"]
Op --> |更新/删除/重置/状态| Perm["require_permission('user:edit'/'user:delete')"]
Perm --> S3["对应服务方法"]
S3 --> R3["success_response(...)"]
Op --> |当前用户信息| U["get_current_user_id()"]
U --> S4["UserService.get_user()"]
S4 --> R4["success_response(...)"]
R1 --> End(["返回"])
R2 --> End
R3 --> End
R4 --> End
```

图表来源
- [service/src/api/v1/user_routes.py:27-252](file://service/src/api/v1/user_routes.py#L27-L252)
- [service/src/api/dependencies.py:45-60](file://service/src/api/dependencies.py#L45-L60)
- [service/src/api/common.py:50-59](file://service/src/api/common.py#L50-L59)

章节来源
- [service/src/api/v1/user_routes.py:27-252](file://service/src/api/v1/user_routes.py#L27-L252)
- [service/src/application/dto/user_dto.py:8-86](file://service/src/application/dto/user_dto.py#L8-L86)

### RBAC 路由（rbac_routes）
- 角色管理
  - 列表（分页+筛选）、创建、详情、更新、删除、为角色分配权限。
- 权限管理
  - 列表（分页+筛选）、创建、删除。
- 权限控制
  - 角色相关操作依赖 role:* 权限；权限相关操作依赖 permission:* 权限。
- 请求参数与响应
  - 使用角色/权限 DTO；列表使用分页响应。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant Role as "角色路由<br/>service/src/api/v1/rbac_routes.py"
participant Perm as "权限路由<br/>service/src/api/v1/rbac_routes.py"
participant Dep as "依赖注入<br/>service/src/api/dependencies.py"
participant Svc as "RBACService<br/>application/services/rbac_service.py"
participant Resp as "统一/分页响应<br/>service/src/api/common.py"
Client->>Role : "GET /api/system/role/list"
Role->>Dep : "require_permission('role : view')"
Role->>Svc : "get_roles(RoleListQueryDTO)"
Svc-->>Role : "roles,total"
Role->>Resp : "page_response(...)"
Resp-->>Client : "分页结果"
Client->>Perm : "POST /api/system/permission"
Perm->>Dep : "require_permission('permission : manage')"
Perm->>Svc : "create_permission(PermissionCreateDTO)"
Svc-->>Perm : "PermissionResponseDTO"
Perm->>Resp : "success_response(..., code=201)"
Resp-->>Client : "创建成功"
```

图表来源
- [service/src/api/v1/rbac_routes.py:33-257](file://service/src/api/v1/rbac_routes.py#L33-L257)
- [service/src/api/dependencies.py:45-60](file://service/src/api/dependencies.py#L45-L60)
- [service/src/api/common.py:50-59](file://service/src/api/common.py#L50-L59)

章节来源
- [service/src/api/v1/rbac_routes.py:33-257](file://service/src/api/v1/rbac_routes.py#L33-L257)
- [service/src/application/dto/rbac_dto.py:8-88](file://service/src/application/dto/rbac_dto.py#L8-L88)

### 菜单路由（menu_routes）
- 功能覆盖
  - 获取完整菜单树、获取当前用户可见菜单、创建、更新、删除菜单。
- 权限控制
  - 菜单树与用户菜单需具备 menu:view 权限；新增/编辑/删除需相应权限。
- 请求参数与响应
  - 使用菜单 DTO；返回统一响应。

```mermaid
sequenceDiagram
participant Client as "客户端"
participant Menu as "菜单路由<br/>service/src/api/v1/menu_routes.py"
participant Dep as "依赖注入<br/>service/src/api/dependencies.py"
participant Svc as "MenuService<br/>application/services/menu_service.py"
participant Resp as "统一响应<br/>service/src/api/common.py"
Client->>Menu : "GET /api/system/menu/tree"
Menu->>Dep : "require_permission('menu : view')"
Menu->>Svc : "get_menu_tree(session)"
Svc-->>Menu : "菜单树"
Menu->>Resp : "success_response(data=tree)"
Resp-->>Client : "返回树形菜单"
```

图表来源
- [service/src/api/v1/menu_routes.py:19-71](file://service/src/api/v1/menu_routes.py#L19-L71)
- [service/src/api/dependencies.py:45-60](file://service/src/api/dependencies.py#L45-L60)
- [service/src/api/common.py:45-47](file://service/src/api/common.py#L45-L47)

章节来源
- [service/src/api/v1/menu_routes.py:19-71](file://service/src/api/v1/menu_routes.py#L19-L71)
- [service/src/application/dto/menu_dto.py:8-56](file://service/src/application/dto/menu_dto.py#L8-L56)

### 依赖注入与权限校验（dependencies）
- 令牌解析与用户身份
  - 从 Authorization 头部提取 Bearer 令牌，解码并校验类型，提取用户 ID。
  - 从数据库获取当前活跃用户，校验账户状态。
- 权限校验
  - require_permission 工厂：若非超级用户，查询用户权限集合，校验是否包含所需权限。
  - require_superuser：仅超级用户可访问。
- 使用场景
  - 认证路由的登出、RBAC/菜单路由的各类操作均依赖上述依赖项。

```mermaid
flowchart TD
A["HTTP Bearer 令牌"] --> B["get_current_user_id()"]
B --> C{"令牌有效且类型正确？"}
C --> |否| E["抛出未授权错误"]
C --> |是| D["从负载提取 sub 作为用户ID"]
D --> F["get_current_active_user()"]
F --> G{"用户存在且激活？"}
G --> |否| E
G --> |是| H["返回用户上下文"]
H --> I["require_permission(code)"]
I --> J{"超级用户？"}
J --> |是| H
J --> |否| K["查询用户权限集合"]
K --> L{"包含所需权限？"}
L --> |否| M["抛出权限不足错误"]
L --> |是| H
```

图表来源
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)

章节来源
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)

### 统一响应与分页（common）
- 统一响应体
  - 字段：code、message、data，默认 code=200、message="success"。
- 分页响应体
  - 字段：total、pageNum、pageSize、totalPage、rows；totalPage 基于 total/pageSize 计算。
- 辅助函数
  - success_response、page_response、error_response，用于快速构造响应。

```mermaid
classDiagram
class UnifiedResponse {
+int code
+string message
+Any data
}
class PageResponse {
+int total
+int pageNum
+int pageSize
+int totalPage
+list rows
}
class ErrorResponse {
+string detail
}
class MessageResponse {
+string message
}
```

图表来源
- [service/src/api/common.py:29-65](file://service/src/api/common.py#L29-L65)

章节来源
- [service/src/api/common.py:29-65](file://service/src/api/common.py#L29-L65)

## 依赖分析
- 路由到依赖
  - 所有 v1 路由模块均依赖统一的依赖注入模块，实现权限与用户身份的集中管理。
- 路由到 DTO
  - 认证、用户、RBAC、菜单路由分别依赖对应 DTO，保证输入输出结构一致。
- 路由到公共组件
  - 统一响应与分页响应被广泛复用，降低重复逻辑。
- 应用到路由
  - 应用工厂在 lifespan 中初始化数据库，在 include_router 时挂载系统路由聚合器。

```mermaid
graph LR
Auth["auth_routes.py"] --> Dep["dependencies.py"]
User["user_routes.py"] --> Dep
RBAC["rbac_routes.py"] --> Dep
Menu["menu_routes.py"] --> Dep
Auth --> Common["common.py"]
User --> Common
RBAC --> Common
Menu --> Common
Auth --> DTO_A["auth_dto.py"]
User --> DTO_U["user_dto.py"]
RBAC --> DTO_R["rbac_dto.py"]
Menu --> DTO_M["menu_dto.py"]
Main["main.py"] --> Sys["v1/__init__.py"]
Sys --> Auth
Sys --> User
Sys --> RBAC
Sys --> Menu
```

图表来源
- [service/src/api/v1/auth_routes.py:10-14](file://service/src/api/v1/auth_routes.py#L10-L14)
- [service/src/api/v1/user_routes.py:10-22](file://service/src/api/v1/user_routes.py#L10-L22)
- [service/src/api/v1/rbac_routes.py:11-24](file://service/src/api/v1/rbac_routes.py#L11-L24)
- [service/src/api/v1/menu_routes.py:9-13](file://service/src/api/v1/menu_routes.py#L9-L13)
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)
- [service/src/api/common.py:29-65](file://service/src/api/common.py#L29-L65)
- [service/src/main.py:90-91](file://service/src/main.py#L90-L91)
- [service/src/api/v1/__init__.py:8-11](file://service/src/api/v1/__init__.py#L8-L11)

章节来源
- [service/src/api/v1/__init__.py:8-11](file://service/src/api/v1/__init__.py#L8-L11)
- [service/src/main.py:90-91](file://service/src/main.py#L90-L91)

## 性能考虑
- 中间件开销
  - 请求日志中间件对每个请求计算耗时并写入日志，建议在生产环境合理设置日志级别，避免高频写盘。
- 依赖链路
  - 依赖注入涉及令牌解码与数据库查询，建议在网关或上游做必要的限流与缓存。
- 分页策略
  - 列表接口统一使用分页 DTO，建议结合索引与 LIMIT/OFFSET 优化数据库查询。
- 响应体积
  - 统一响应体包含 code/message/data，建议在大列表场景仅返回必要字段，避免过度序列化。

## 故障排查指南
- 参数验证失败（422）
  - 全局异常处理器捕获 RequestValidationError，返回包含 errors 的统一错误响应。
- 未授权/权限不足
  - 依赖注入抛出未授权或权限不足异常，确认 Bearer 令牌有效性与权限分配。
- 服务器内部错误（500）
  - 未捕获异常统一转换为 500 错误响应，检查日志定位问题。
- 健康检查
  - GET /health 返回应用健康状态与版本号，用于探活与版本核对。

章节来源
- [service/src/main.py:68-82](file://service/src/main.py#L68-L82)
- [service/src/api/dependencies.py:16-72](file://service/src/api/dependencies.py#L16-L72)

## 结论
本表现层以 v1 路由聚合器为核心，结合统一的依赖注入与响应规范，实现了认证、用户、RBAC、菜单四大领域的清晰分离与一致交互体验。通过权限校验与中间件集成，保障了安全性与可观测性。遵循本文的路由设计模式与最佳实践，可高效扩展新功能并保持代码一致性。

## 附录
- API 版本管理
  - 应用标题、版本与文档路径由配置与常量共同决定，系统前缀统一挂载路由，便于未来版本演进。
- 常用路径参考
  - 认证：登录/注册/刷新/登出
  - 用户：列表/创建/详情/更新/删除/批量删除/重置密码/状态变更/当前用户信息/密码修改
  - 角色：列表/创建/详情/更新/删除/为角色分配权限
  - 权限：列表/创建/删除
  - 菜单：菜单树/用户可见菜单/创建/更新/删除

章节来源
- [service/src/config/settings.py:47-51](file://service/src/config/settings.py#L47-L51)
- [service/src/core/constants.py:4-6](file://service/src/core/constants.py#L4-L6)
- [service/src/api/v1/auth_routes.py:19-86](file://service/src/api/v1/auth_routes.py#L19-L86)
- [service/src/api/v1/user_routes.py:27-252](file://service/src/api/v1/user_routes.py#L27-L252)
- [service/src/api/v1/rbac_routes.py:33-257](file://service/src/api/v1/rbac_routes.py#L33-L257)
- [service/src/api/v1/menu_routes.py:19-71](file://service/src/api/v1/menu_routes.py#L19-L71)