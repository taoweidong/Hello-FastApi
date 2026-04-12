# RBAC重构 — 剩余工作计划

## 产品概述

按照已有RBAC重构计划继续实施，跳过已完成的阶段1-3核心架构部分，聚焦剩余未完成的工作。

## 核心功能

### 后端遗留项修复

- IPRule模型补充标准化审计字段（creator_id/modifier_id/created_time/updated_time/description）
- 清理SystemLogEntity别名（entities/log.py中的兼容性别名）

### 后端单元测试（阶段4）

- 编写角色服务、菜单服务、部门服务、日志服务、系统配置服务、认证服务的单元测试
- 补充RBAC权限相关集成测试

### 前端重构（阶段5）

- API层从单一system.ts拆分为独立模块API（函数式风格，不引入BaseApi类）
- 菜单管理适配新API调用
- 角色管理适配新API调用
- 用户管理适配新字段和布局
- 部门管理适配新字段和树形表格
- 日志管理适配统一日志接口
- 权限管理页面适配新RBAC（原permission页面改为基于菜单权限）
- Store/Router/权限工具适配

### 前后端联调（阶段6）

- RBAC权限流程端到端验证
- 各模块CRUD联调

## 已完成情况

### 阶段1: ORM模型层 — ✅ 100% 完成
- 所有模型已适配新schema（UUID char(32) ID、审计字段等）
- permission.py, role_permission_link.py, operation_log.py 已删除
- menu_meta.py, system_config.py 新文件已创建

### 阶段2: 实体+仓储层 — ✅ 100% 完成
- 所有实体和仓储接口/实现已完成
- permission相关文件已删除

### 阶段3: DTO+Service+Router — ~95% 完成
- 所有DTO、Service、Router已适配新结构
- require_permission已改为基于Menu.menu_type==2和menu.name检查
- require_menu_permission新增基于API path+method的权限检查

## Tech Stack

- 后端：FastAPI + classy-fastapi + SQLModel + FastCRUD + DDD分层架构
- 前端：Vue 3 + vue-pure-admin + Pinia + Element Plus + TSX Hook模式
- 数据库：MySQL 8.0 + SQLModel ORM
- 认证：JWT（AccessToken + RefreshToken）
- 测试：pytest + pytest-asyncio + httpx

## Implementation Approach

### 后端遗留项

IPRule模型缺少审计字段，需与其它模型保持一致。SystemLogEntity别名应在代码中清理，但保持向后兼容的导出。

### 后端单元测试

采用与现有test_user_service.py相同的模式：使用AsyncMock模拟仓储，测试服务层业务逻辑。RBAC权限测试重点验证require_permission和require_menu_permission两个依赖工厂。

### 前端重构策略

前端已有较为完整的页面框架（菜单管理有form.vue支持三种类型、角色管理有菜单权限树、用户管理有部门树+列表），主要工作是：

1. **API层拆分**：从system.ts单一文件拆分为独立模块API文件，但暂不实现BaseApi类（当前项目API风格是函数式而非类式，强行改为BaseApi模式收益不大且风险高）
2. **页面组件适配新接口**：现有页面已基本适配新RBAC（menu_type三种类型、meta嵌套对象、method字段等），需微调API调用和数据格式
3. **权限控制适配**：hasPerms已基于permissions（菜单name）工作，auth.ts已适配新格式，主要需确认前端按钮权限检查与后端一致

### 关键决策

1. **不实现BaseApi类**：当前项目API层是函数式导出（`export const xxx = () => http.request(...)`），改为类式BaseApi模式需要大量重构且与vue-pure-admin的现有模式不匹配。保持函数式风格，仅按模块拆分文件。
2. **不强制使用to_domain/from_domain**：当前服务层直接操作ORM模型的模式在该项目中是可接受的务实选择，强行引入领域实体转换层会增加复杂度但无实际业务收益。
3. **保留permission页面并重命名**：原permission/index.vue已实现角色+菜单权限树功能，与新RBAC方案高度吻合，保留并优化而非删除重建。

## Directory Structure

### 后端变更

```
service/src/
├── infrastructure/database/models/
│   └── ip_rule.py                    # [MODIFY] 补充审计字段(creator_id/modifier_id/created_time/updated_time/description)
├── domain/entities/
│   ├── log.py                        # [MODIFY] 清理SystemLogEntity别名注释
│   └── ip_rule.py                    # [MODIFY] 补充审计字段
├── domain/repositories/
│   └── ip_rule_repository.py         # [MODIFY] 接口适配审计字段(如需)
├── infrastructure/repositories/
│   └── ip_rule_repository.py         # [MODIFY] 实现适配审计字段
├── application/dto/                   # ip_rule DTO如需适配
├── application/services/
│   └── ip_rule_service.py            # [MODIFY] 适配审计字段
├── api/v1/
│   └── ip_rule_router.py             # [MODIFY] 适配审计字段
└── tests/
    ├── unit/
    │   ├── test_role_service.py      # [NEW] 角色服务单元测试
    │   ├── test_menu_service.py      # [NEW] 菜单服务单元测试
    │   ├── test_department_service.py # [NEW] 部门服务单元测试
    │   ├── test_log_service.py       # [NEW] 日志服务单元测试
    │   ├── test_system_config_service.py # [NEW] 系统配置服务单元测试
    │   └── test_auth_service.py      # [NEW] 认证服务单元测试
    └── integration/
        └── test_rbac.py              # [NEW] RBAC权限流程集成测试
```

### 前端变更

```
web/src/
├── api/
│   ├── system/                       # [NEW] 从system.ts拆分的独立模块API
│   │   ├── user.ts                   # [NEW] 用户管理API
│   │   ├── role.ts                   # [NEW] 角色管理API
│   │   ├── menu.ts                   # [NEW] 菜单管理API
│   │   ├── dept.ts                   # [NEW] 部门管理API
│   │   ├── log.ts                    # [NEW] 日志管理API
│   │   └── config.ts                 # [NEW] 系统配置API
│   └── system.ts                     # [MODIFY] 保留但改为从system/重新导出，逐步废弃
├── views/system/
│   ├── menu/
│   │   ├── index.vue                 # [MODIFY] 适配新API调用，移除"仅演示"提示
│   │   ├── form.vue                  # [MODIFY] 微调meta字段映射
│   │   └── utils/hook.tsx            # [MODIFY] 适配新API导入路径
│   ├── role/
│   │   ├── index.vue                 # [MODIFY] 移除"仅演示"提示，适配新API
│   │   ├── form.vue                  # [MODIFY] 保持现有角色表单
│   │   └── utils/hook.tsx            # [MODIFY] 适配新API导入路径
│   ├── user/
│   │   ├── index.vue                 # [MODIFY] 移除"仅演示"提示，适配新字段
│   │   ├── tree.vue                  # [MODIFY] 适配新API
│   │   └── utils/hook.tsx            # [MODIFY] 适配新API、新字段
│   ├── dept/
│   │   ├── index.vue                 # [MODIFY] 移除"仅演示"提示，适配新字段
│   │   ├── form.vue                  # [MODIFY] 适配新字段(modeType/code/rank/autoBind)
│   │   └── utils/hook.tsx            # [MODIFY] 适配新API、新字段
│   ├── permission/
│   │   ├── index.vue                 # [MODIFY] 适配新API（角色菜单权限树）
│   │   └── hook.tsx                  # [MODIFY] 适配getRoleMenu/getRoleMenuIds/saveRoleMenu
│   ├── config/
│   │   ├── index.vue                 # [MODIFY] 适配新API
│   │   └── hook.tsx                  # [MODIFY] 适配新API
│   └── ip-rule/
│       ├── index.vue                 # [MODIFY] 适配新API
│       └── hook.tsx                  # [MODIFY] 适配新API
├── views/monitor/
│   ├── logs/
│   │   ├── login/index.vue           # [MODIFY] 适配新API
│   │   ├── operation/index.vue       # [MODIFY] 适配新API
│   │   └── system/
│   │       ├── index.vue             # [MODIFY] 适配新API
│   │       └── hook.tsx              # [MODIFY] 适配新API
│   └── online/index.vue              # [MODIFY] 适配新API
├── store/
│   ├── modules/user.ts               # [MODIFY] 修复SET_MENUS→SET_PERMS方法名问题
│   └── types.ts                      # [MODIFY] 确认userType包含permissions字段
└── utils/
    └── auth.ts                       # [MODIFY] 确认permissions字段正确存储/读取
```

## Implementation Notes

- IPRule审计字段变更需同步更新entity、repository接口、repository实现、DTO、service、router全链路
- 前端API拆分时，system.ts先保留作为重新导出中转，避免一次性删除导致全项目编译错误
- 前端页面移除"仅演示，操作后不生效"提示，因为CRUD操作已经对接真实后端
- store/modules/user.ts中有SET_MENUS方法但userType中没有menus字段，需修复为SET_PERMS
- 测试文件遵循现有模式：unit测试用AsyncMock，integration测试用SQLite内存数据库+AsyncClient

## Todo List

- [ ] 补充IPRule模型审计字段(creator_id/modifier_id/created_time/updated_time/description)及全链路适配
- [ ] 修复store/modules/user.ts中SET_MENUS→SET_PERMS方法名及userType类型定义
- [ ] 前端API层从system.ts拆分为system/目录下独立模块文件(user/role/menu/dept/log/config)
- [ ] 适配前端所有页面组件API调用路径、移除演示提示、适配新字段
- [ ] 编写角色/菜单/部门/日志/系统配置/认证服务的单元测试
- [ ] 编写RBAC权限流程集成测试(require_permission/require_menu_permission/动态路由)
