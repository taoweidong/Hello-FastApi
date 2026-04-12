---
name: rbac-remaining-tasks
overview: 基于rbac-refactoring.md计划，跳过已完成的阶段1-3大部分功能，聚焦剩余未完成项：后端缺陷修复（IPRule审计字段、MenuRepository缺失方法）、前端重构（阶段5全部）、后端测试（阶段4）、前后端联调（阶段6）
todos:
  - id: fix-backend-defects
    content: "修复后端遗留缺陷: IPRule审计字段、MenuRepository.get_by_name、SystemConfigRepository.count和分页get_all"
    status: completed
  - id: update-backend-tests
    content: 更新后端单元测试, 适配新RBAC模型和修复后的接口
    status: completed
    dependencies:
      - fix-backend-defects
  - id: frontend-api-base
    content: 创建BaseApi基础类和独立模块API目录(web/src/api/base.ts + system/*.ts)
    status: completed
  - id: frontend-constants-utils
    content: 创建公共常量constants.ts和渲染工具render.tsx, 修改enums.ts和hooks.ts
    status: completed
    dependencies:
      - frontend-api-base
  - id: frontend-menu-refactor
    content: "重构菜单管理: 左右分栏布局(tree+edit), MenuMeta嵌入编辑, 三级菜单类型"
    status: completed
    dependencies:
      - frontend-constants-utils
  - id: frontend-role-user-dept
    content: 重构角色管理(菜单权限树)、用户管理(部门树+列表)、部门管理(树形表格)
    status: completed
    dependencies:
      - frontend-menu-refactor
  - id: frontend-logs-store-router
    content: 创建日志管理页面, 适配Store/Router/auth, 全链路联调验证
    status: completed
    dependencies:
      - frontend-role-user-dept
---

## 产品概述

继续执行RBAC重构计划，跳过已完成的功能，完成剩余的后端缺陷修复、后端单元测试、前端重构和前后端联调。

## 核心功能

### 后端缺陷修复

- IPRule模型补全审计字段(creator_id/modifier_id/created_time/updated_time/description)
- IPRuleEntity适配新审计字段
- MenuRepositoryInterface添加get_by_name方法及其实现
- SystemConfigRepositoryInterface添加count和分页get_all方法及其实现

### 后端单元测试

- 更新现有测试适配新RBAC模型
- 新增RBAC权限相关测试

### 前端重构(参照xadmin-client)

- API层拆分: BaseApi基础类 + 独立模块API(system/user.ts, role.ts, menu.ts, dept.ts, log.ts, system_config.ts)
- 公共工具: constants.ts(MenuChoices/MethodChoices/ModeChoices), render.tsx
- 菜单管理: 左右分栏布局(tree + edit), 菜单类型三级分类(DIRECTORY/MENU/PERMISSION), MenuMeta嵌入编辑
- 角色管理: 菜单权限树组件(el-tree+checkbox)
- 用户管理: 左侧部门树+右侧列表
- 部门管理: RePlusPage树形表格
- 日志管理: 登录日志和操作日志页面
- Store/Router/auth适配新菜单路由和权限结构

### 前后端联调

- 认证流程、菜单管理、角色管理、用户管理、部门管理、日志管理、系统配置全链路验证

## Tech Stack

- 后端: FastAPI + classy-fastapi + SQLModel + FastCRUD + DDD分层架构
- 前端: Vue 3 + vue-pure-admin + Pinia + Element Plus + TSX Hook模式
- 数据库: MySQL 8.0 + SQLModel ORM
- 认证: JWT (AccessToken + RefreshToken)
- 参考项目: xadmin-client (E:\GitHub\xadmin\xadmin-client-nineaiyu)

## Implementation Approach

采用**先修后建**策略: 先完成后端遗留缺陷修复, 再进行前端大规模重构, 最后联调验证。前端重构按依赖顺序推进: 公共基础(API层/常量/工具) → 页面重构(菜单→角色→用户→部门→日志) → Store/Router适配 → 联调。

## Implementation Notes

- MenuService.create_menu调用self.menu_repo.get_by_name(), 但MenuRepositoryInterface和MenuRepository均未定义此方法, 需补全
- SystemConfigService.get_configs调用self.config_repo.count()和分页get_all(), 但SystemConfigRepositoryInterface仅定义了无参数get_all, 需补全count和分页参数
- IPRule模型/entity仍使用created_at(DateTime)而非created_time(DateTime(6)), 需统一审计字段
- 前端menu/utils/enums.ts仍使用旧菜单类型(0=菜单/1=iframe/2=外链/3=按钮), 需改为DIRECTORY(0)/MENU(1)/PERMISSION(2)
- 前端api/system.ts仍为单一文件, 需拆分为BaseApi继承模式
- 前端视图页面仍为旧布局, 需参照xadmin-client重构

## Directory Structure

### 后端修复文件

```
service/src/
├── infrastructure/database/models/
│   └── ip_rule.py                    # [MODIFY] 添加creator_id/modifier_id/created_time(DateTime(6))/updated_time(DateTime(6))/description, 移除created_at
├── domain/entities/
│   └── ip_rule.py                    # [MODIFY] created_at→created_time, 新增modifier_id/updated_time/description
├── domain/repositories/
│   ├── menu_repository.py            # [MODIFY] 添加get_by_name抽象方法
│   ├── system_config_repository.py   # [MODIFY] 添加count和分页get_all抽象方法
│   └── ip_rule_repository.py         # [MODIFY] 适配新审计字段
├── infrastructure/repositories/
│   ├── menu_repository.py            # [MODIFY] 实现get_by_name
│   ├── system_config_repository.py   # [MODIFY] 实现count和分页get_all
│   └── ip_rule_repository.py         # [MODIFY] 适配新审计字段
├── application/services/
│   └── ip_rule_service.py            # [MODIFY] 适配新审计字段
├── infrastructure/http/
│   └── request_logging_middleware.py  # [VERIFY] 确认日志中间件适配新字段
```

### 前端重构文件

```
web/src/
├── api/
│   ├── base.ts                       # [NEW] BaseApi基础类, 提供list/retrieve/create/partialUpdate/destroy标准CRUD方法
│   ├── system/                       # [NEW] 从system.ts拆分的独立模块目录
│   │   ├── user.ts                   # [NEW] UserApi extends BaseApi
│   │   ├── role.ts                   # [NEW] RoleApi extends BaseApi
│   │   ├── menu.ts                   # [NEW] MenuApi extends BaseApi
│   │   ├── dept.ts                   # [NEW] DeptApi extends BaseApi
│   │   ├── log.ts                    # [NEW] LogApi, 统一日志API
│   │   └── system_config.ts          # [NEW] SystemConfigApi extends BaseApi
│   ├── system.ts                     # [MODIFY→保留] 逐步迁移, 最终可删除或保留为兼容层
│   ├── user.ts                       # [MODIFY] 登录响应适配
│   └── routes.ts                     # [MODIFY] 动态路由格式适配
├── views/system/
│   ├── constants.ts                  # [NEW] MenuChoices(DIRECTORY:0/MENU:1/PERMISSION:2), MethodChoices, ModeChoices
│   ├── render.tsx                    # [NEW] renderOption(Segmented渲染), renderSwitch(开关渲染)
│   ├── hooks.ts                      # [MODIFY] 添加formatHigherDeptOptions, customRolePermissionOptions等
│   ├── menu/
│   │   ├── index.vue                 # [MODIFY] 左右分栏布局(tree + edit)
│   │   ├── components/
│   │   │   ├── tree.vue              # [NEW] 菜单树组件, 搜索/展开/折叠
│   │   │   └── edit.vue              # [NEW] 菜单编辑表单, menu_type切换/MenuMeta嵌套编辑
│   │   └── utils/
│   │       ├── hook.tsx              # [MODIFY] 适配新菜单结构
│   │       ├── types.ts              # [MODIFY] FormItemProps含meta嵌套
│   │       ├── rule.ts               # [MODIFY] dirFormRules/menuFormRules/permissionFormRules
│   │       └── enums.ts              # [MODIFY] 菜单类型改为DIRECTORY/MENU/PERMISSION
│   ├── role/
│   │   ├── index.vue                 # [MODIFY] RePlusPage + 菜单权限树弹窗
│   │   ├── components/
│   │   │   └── form.vue              # [NEW] 菜单权限树组件, el-tree+checkbox
│   │   └── utils/
│   │       └── hook.tsx              # [MODIFY] 菜单权限树数据加载
│   ├── user/
│   │   ├── index.vue                 # [MODIFY] 左侧部门树+右侧列表布局
│   │   ├── components/
│   │   │   └── tree.vue              # [NEW/MODIFY] 部门树组件
│   │   └── utils/
│   │       └── hook.tsx              # [MODIFY] 适配新用户结构
│   ├── dept/
│   │   ├── index.vue                 # [MODIFY] 树形表格模式
│   │   └── utils/
│   │       └── hook.tsx              # [MODIFY] isTree树形/父级级联选择
│   └── logs/                         # [NEW] 日志管理
│       ├── login/                    # [NEW] 登录日志页面
│       └── operation/                # [NEW] 操作日志页面
├── store/modules/
│   ├── user.ts                       # [MODIFY] 适配新登录响应
│   └── permission.ts                 # [MODIFY] 适配新菜单路由结构
├── router/
│   └── utils.ts                      # [MODIFY] 动态路由处理适配新格式
└── utils/
    └── auth.ts                       # [MODIFY] 适配新权限存储
```

## Agent Extensions

### SubAgent

- **code-explorer**: 探索xadmin-client参考项目的关键设计模式和组件结构, 提取可复用的前端代码模式

### Skill

- **python-code-quality**: 确保后端Python代码质量, 使用类型注解和SOLID原则