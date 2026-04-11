---
name: fullstack-integration-test-and-fix
overview: 前后端功能联调 - 使用 testing 环境配置启动，全新数据库初始化，逐页面测试所有功能，修复发现的问题
todos:
  - id: prepare-env
    content: 删除旧的 sql/test.db，确保使用全新数据库；确认 .env.testing 配置正确（SQLite + 测试密钥）
    status: pending
  - id: start-backend
    content: 设置 APP_ENV=testing 启动后端服务，自动建表；然后通过 CLI 初始化种子数据（superuser + rbac + menus + logs）
    dependencies:
      - prepare-env
    status: pending
  - id: start-frontend
    content: 安装前端依赖并启动前端开发服务器（端口8848）
    status: pending
  - id: verify-services
    content: 验证后端健康检查接口和前端页面可访问性
    dependencies:
      - start-backend
      - start-frontend
    status: pending
  - id: test-login
    content: 使用 Playwright 测试登录页（登录/注册/Token刷新），获取认证状态
    dependencies:
      - verify-services
    status: pending
  - id: test-user-mgmt
    content: 测试用户管理页面：页面加载 + 全部按钮（新增/修改/删除/批量删除/重置密码/分配角色/状态开关/搜索）
    dependencies:
      - test-login
    status: pending
  - id: test-role-mgmt
    content: 测试角色管理页面：页面加载 + 全部按钮（新增/修改/删除/权限面板/保存菜单权限/状态开关/搜索）
    dependencies:
      - test-login
    status: pending
  - id: test-menu-mgmt
    content: 测试菜单管理页面：页面加载 + 全部按钮（新增/修改/新增子菜单/删除）
    dependencies:
      - test-login
    status: pending
  - id: test-dept-mgmt
    content: 测试部门管理页面：页面加载 + 全部按钮（新增/修改/新增子部门/删除）
    dependencies:
      - test-login
    status: pending
  - id: test-online-user
    content: 测试在线用户页面：页面加载 + 搜索/强退按钮，修复前端 hook 未调用 forceOffline API
    dependencies:
      - test-login
    status: pending
  - id: test-log-pages
    content: 测试日志页面（登录/操作/系统日志）：页面加载 + 搜索/批量删除/清空按钮，修复前端 hook 未调用实际 API
    dependencies:
      - test-login
    status: pending
  - id: test-perm-pages
    content: 测试权限管理页面：页面权限/按钮权限功能验证
    dependencies:
      - test-login
    status: pending
  - id: test-account-pages
    content: 测试账户设置/关于/引导页面功能
    dependencies:
      - test-login
    status: pending
  - id: fix-all-issues
    content: 修复所有发现的前后端问题，确保代码质量
    dependencies:
      - test-user-mgmt
      - test-role-mgmt
      - test-menu-mgmt
      - test-dept-mgmt
      - test-online-user
      - test-log-pages
      - test-perm-pages
      - test-account-pages
    status: pending
---

## 产品概述

Hello-FastApi 是一个基于 Vue3 + FastAPI 的全栈中后台管理系统，包含 JWT 双令牌认证、RBAC 权限控制、用户/角色/菜单/部门管理、日志监控等功能模块。

## 核心目标

1. **启动服务** - 修复环境配置，启动前后端服务
2. **逐页面功能测试** - 不仅验证页面能否加载，更要测试每个按钮交互是否正常
3. **前后端联调验证** - 确认前端 API 调用与后端接口契约一致
4. **修复所有问题** - 集中修复测试中发现的前后端问题

## 技术栈

- 后端: Python 3.10+ / FastAPI / SQLModel / SQLite(aiosqlite) / JWT(python-jose) / bcrypt
- 前端: Vue 3.5+ / Vite 8+ / TypeScript / Element Plus / Pinia / TailwindCSS
- 工具: uv(Python包管理) / pnpm(前端包管理) / Playwright(浏览器自动化测试)

## 实施方案

### 整体策略

按"环境准备 → 启动服务(测试配置) → 登录认证 → 逐页面深度测试 → 集中修复"的流程推进。每个页面测试包含：
1. 页面是否能正常加载渲染
2. 每个按钮点击是否能触发正确的前后端交互
3. API 请求与响应是否符合预期

### 测试流程

#### 第一阶段：环境准备与服务启动

1. **删除旧数据库**: 删除 `service/sql/test.db`，确保从全新状态开始
2. **确认 testing 配置**: `.env.testing` 已配置 SQLite（`sqlite+aiosqlite:///./sql/test.db`），无需修改
3. **启动后端服务**: 设置环境变量 `APP_ENV=testing` 启动后端，lifespan 自动建表
4. **初始化种子数据**: 依次执行 CLI 命令：
   - `python -m scripts.cli createsuperuser -u admin -p admin123 -e admin@example.com` — 创建管理员
   - `python -m scripts.cli seedrbac` — 初始化角色和权限
   - `python -m scripts.cli seeddata` — 初始化菜单、日志等测试数据
5. **启动前端服务**: `pnpm install && pnpm dev`，端口 8848
6. **验证服务**: 确认后端健康检查接口返回正常，前端页面可访问

> **为什么用 testing 配置而不是 development？**
> - testing 配置使用独立的 `test.db`，与开发数据库 `dev.db` 隔离
> - 每次测试前删除 `test.db` 即可获得全新数据，保证测试一致性
> - testing 配置的 JWT 密钥、限流等参数更宽松，适合联调测试

#### 第二阶段：登录认证

- 使用 admin/admin123 登录
- 验证 Token 获取和刷新机制
- 截图记录登录成功状态

#### 第三阶段：逐页面深度测试

**用户管理 (8个按钮)**
| 按钮 | API | HTTP方法+URL |
|---|---|---|
| 新增用户 | createUser | POST /user/create |
| 修改用户 | updateUser | PUT /user/{id} |
| 删除用户 | deleteUser | DELETE /user/{id} |
| 批量删除 | batchDeleteUser | POST /user/batch-delete |
| 重置密码 | resetPassword | PUT /user/{id}/reset-password |
| 分配角色 | assignUserRole | POST /user/assign-role |
| 状态开关 | updateUserStatus | PUT /user/{id}/status |
| 搜索/重置 | getUserList | POST /user |

**角色管理 (7个按钮)**
| 按钮 | API | HTTP方法+URL |
|---|---|---|
| 新增角色 | createRole | POST /role/create |
| 修改角色 | updateRole | PUT /role/{id} |
| 删除角色 | deleteRole | DELETE /role/{id} |
| 权限面板 | getRoleMenuIds | POST /role-menu-ids |
| 保存菜单权限 | saveRoleMenu | POST /role/{id}/menu |
| 状态开关 | updateRoleStatus | PUT /role/{id}/status |
| 搜索/重置 | getRoleList | POST /role |

**菜单管理 (4个按钮)**
| 按钮 | API | HTTP方法+URL |
|---|---|---|
| 新增菜单 | createMenu | POST /menu/create |
| 修改菜单 | updateMenu | PUT /menu/{id} |
| 新增子菜单 | createMenu | POST /menu/create |
| 删除菜单 | deleteMenu | DELETE /menu/{id} |

**部门管理 (4个按钮)**
| 按钮 | API | HTTP方法+URL |
|---|---|---|
| 新增部门 | createDept | POST /dept/create |
| 修改部门 | updateDept | PUT /dept/{id} |
| 新增子部门 | createDept | POST /dept/create |
| 删除部门 | deleteDept | DELETE /dept/{id} |

**在线用户 (2个按钮)**
| 按钮 | API | HTTP方法+URL | 问题 |
|---|---|---|---|
| 搜索 | getOnlineUserList | POST /online-logs | - |
| 强退 | forceOffline | POST /online-logs/force-offline | ⚠️ 前端hook未调用API |

**日志页面 (6个按钮，跨3个页面)**
| 按钮 | API | HTTP方法+URL | 问题 |
|---|---|---|---|
| 登录日志-清空 | clearLoginLogs | POST /login-logs/clear | ⚠️ 前端hook未调用API |
| 登录日志-批量删除 | batchDeleteLoginLogs | POST /login-logs/batch-delete | ⚠️ 前端hook未调用API |
| 操作日志-清空 | clearOperationLogs | POST /operation-logs/clear | ⚠️ 前端hook未调用API |
| 操作日志-批量删除 | batchDeleteOperationLogs | POST /operation-logs/batch-delete | ⚠️ 前端hook未调用API |
| 系统日志-清空 | clearSystemLogs | POST /system-logs/clear | ⚠️ 前端hook未调用API |
| 系统日志-批量删除 | batchDeleteSystemLogs | POST /system-logs/batch-delete | ⚠️ 前端hook未调用API |

**权限页面** - 验证页面权限和按钮权限功能

**账户设置** - 个人信息/安全日志（部分为前端演示性质）

### 关键技术决策

1. **使用 testing 环境配置**: 通过 `APP_ENV=testing` 加载 `.env.testing`，使用独立 `sql/test.db`，与开发数据隔离
2. **全新数据库初始化**: 每次启动前删除 `test.db`，lifespan 自动建表 + CLI 初始化种子数据，保证数据全新且一致
3. **Playwright 自动化**: 逐页面访问、截图、点击交互按钮、填写表单、提交验证
4. **前端 Hook 修复**: 多个页面 hook 中只显示 message 未调用实际 API，需补全 API 调用
5. **后端接口补全**: 为 `forceOffline` 等前端已调用但后端缺失的接口添加实现
6. **权限校验补全**: 部门/日志管理路由缺少 `require_permission` 权限校验
7. **代码质量**: 使用 python-code-quality skill 确保后端修复代码质量

### 实施注意事项

- 启动后端时设置 `APP_ENV=testing`（Windows: `set APP_ENV=testing` / Linux: `export APP_ENV=testing`）
- 每次启动前删除 `service/sql/test.db` 确保数据库全新
- lifespan 自动建表，但种子数据需要手动通过 CLI 命令初始化
- CLI 命令也需要在 `APP_ENV=testing` 环境下执行，确保写入 test.db
- 使用 admin 账号登录（admin/admin123）
- 删除操作需谨慎，避免删除关键数据；新增测试数据后及时清理
- 每个按钮测试后截图记录结果
- 前端 `pnpm install` 可能耗时较长，需提前执行
- Playwright 截图用于验证页面渲染状态，console 日志用于捕获 API 错误
- 修复问题时遵循现有 DDD 四层架构模式，不引入新架构
- testing 配置 CORS_ORIGINS 仅为 `http://localhost:3000`，需确认前端 8848 端口能正常访问后端

## 已知问题清单

### 环境配置
1. `.env.testing` 的 CORS_ORIGINS 仅为 `http://localhost:3000`，前端实际运行在 8848 端口，需添加 `http://localhost:8848`
2. testing 环境未配置 Redis，相关功能可能不可用（非阻塞性）

### 后端问题
3. 角色列表接口 `role_routes.py` 中引用了 `role.createTime`（应为 `role.created_at`）
4. `PermissionRepository.get_all` 方法签名可能不匹配 `auth_service.py` 的调用方式
5. 前端调用了不存在的后端接口 `forceOffline`
6. 部门管理路由缺少 `require_permission` 权限校验
7. 日志管理路由删除/清空接口缺少 `require_permission`

### 前端问题
8. 在线用户 `web/src/views/monitor/online/hook.tsx` 中 `handleOffline` 只显示 message 未调用 `forceOffline` API
9. 登录日志 `web/src/views/monitor/logs/login/hook.tsx` 中 `onbatchDel`/`clearAll` 只显示 message 未调用实际 API
10. 操作日志 `web/src/views/monitor/logs/operation/hook.tsx` 同上
11. 系统日志 `web/src/views/monitor/logs/system/hook.tsx` 同上
12. 前端 `system.ts` 日志清空接口方法可能使用 DELETE 应改为 POST

## 需修改的文件

```
service/
├── .env.testing                        # [MODIFY] CORS_ORIGINS 添加 http://localhost:8848
├── src/api/v1/
│   ├── monitor_router.py               # [MODIFY] 添加 force-offline 接口实现
│   ├── dept_router.py                  # [MODIFY] 添加 require_permission 权限校验
│   ├── log_router.py                   # [MODIFY] 删除/清空接口添加 require_permission
│   ├── role_routes.py                  # [MODIFY] 修复 createTime → created_at 字段映射
│   ├── auth_routes.py                  # [MODIFY] 修复 API 兼容性问题
│   ├── permission_routes.py            # [MODIFY] 修复分页响应格式
│   ├── menu_routes.py                  # [MODIFY] 可能需要修复
│   └── user_routes.py                  # [MODIFY] 可能需要修复字段映射
├── src/application/services/
│   ├── auth_service.py                 # [MODIFY] 修复 get_all 调用方式
│   └── permission_service.py           # [MODIFY] 修复 get_all 方法签名
├── src/infrastructure/repositories/
│   └── permission_repository.py        # [MODIFY] 修复 get_all 方法签名
└── sql/test.db                         # [DELETE] 删除旧库，启动时自动重建

web/
├── src/api/system.ts                   # [MODIFY] 修复日志清空接口方法（DELETE→POST）
├── src/views/monitor/online/hook.tsx   # [MODIFY] 补全 forceOffline API 调用
├── src/views/monitor/logs/login/hook.tsx    # [MODIFY] 补全批量删除/清空 API 调用
├── src/views/monitor/logs/operation/hook.tsx # [MODIFY] 补全批量删除/清空 API 调用
├── src/views/monitor/logs/system/hook.tsx    # [MODIFY] 补全批量删除/清空 API 调用
└── 其他前端文件视测试结果修改
```

## 工具与扩展

### MCP

- **Playwright MCP Server**
- Purpose: 逐页面自动化浏览器测试，访问页面、截图验证、点击按钮、填写表单、捕获 console 错误和 API 响应
- Expected outcome: 获得每个页面的截图和 console 日志，识别所有前后端联调问题

### Skill

- **Browser Automation** - 自动化浏览器操作，逐页面测试前后端联调功能
- **python-code-quality** - 确保后端修复代码符合高质量 Python 标准（类型注解、SOLID 原则）
