  ---
name: frontend-backend-optimization-v4
overview: 四项优化：1)用户管理移除部门树；2)菜单管理移除权限功能；3)字典管理树节点增加新增子项(参照PureAdmin参考截图)；4)后端日志排除refresh-token等接口
design:
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 16px
      weight: 600
    subheading:
      size: 14px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#409EFF"
      - "#337ECC"
    background:
      - "#FFFFFF"
      - "#F5F7FA"
      - "#F0F2F5"
    text:
      - "#303133"
      - "#606266"
      - "#909399"
    functional:
      - "#67C23A"
      - "#E6A23C"
      - "#F56C6C"
      - "#909399"
todos:
  - id: user-remove-tree
    content: 使用 [skill:frontend-dev] 修改 user/index.vue：删除 tree import/treeRef/左栏 flex 布局/树组件标签，改为全宽单栏；useUser 调用改为单参数
    status: pending
  - id: user-clean-hook
    content: 使用 [skill:frontend-dev] 清理 user/utils/hook.tsx：函数签名改单参数，删除 treeData/treeLoading/onTreeSelect/deptApi→treeData/resetForm onTreeReset
    status: pending
    dependencies:
      - user-remove-tree
  - id: menu-filter-tree
    content: 使用 [skill:frontend-dev] 修改 menu/components/tree.vue：computed 过滤 menuType===2 权限节点，移除权限 info tag 渲染分支
    status: pending
  - id: menu-simplify-form
    content: 使用 [skill:frontend-dev] 精简 menu/form.vue 和 edit.vue：移除权限 type=2 选项、HTTP方法字段(methodOptions import)、case:2 规则分支
    status: pending
    dependencies:
      - menu-filter-tree
  - id: menu-clean-hook-cols
    content: 使用 [skill:frontend-dev] 清理 menu/utils 下文件：hook.tsx 删除权限标识列(prop:"method") 和 payload.method 字段；enums.ts 注释 methodOptions
    status: pending
    dependencies:
      - menu-filter-tree
  - id: dict-add-context-action
    content: 使用 [skill:frontend-dev] 修改 dictionary/index.vue：树节点 el-dropdown-menu 第三项新增"新增子项"(AddFill图标)，绑定 openAddDictDetailForNode(data)
    status: pending
  - id: dict-extend-hook
    content: 使用 [skill:frontend-dev] 修改 dictionary/utils/hook.tsx：新增 openAddDictDetailForNode(parentNode) 方法（设 selectedDictType 后复用 openAddDictDetail 逻辑），return 导出
    status: pending
    dependencies:
      - dict-add-context-action
  - id: log-middleware-exclude-paths
    content: 使用 [skill:python-code-quality] 修改 request_logging_middleware.py：模块级定义 _SKIP_LOG_PATH_PREFIXES(frozenset)，添加 _should_skip_log() 静态方法，dispatch 第111行加 and not self._should_skip_log() 条件
    status: pending
---

## 产品概述

对前端三个系统管理页面进行 UI 精简/功能完善，并对后端操作日志中间件增加路径排除机制以减少无效审计记录。

## 核心功能

### 需求一：用户管理页移除部门树（UI 布局精简）

- 移除 `web/src/views/system/user/index.vue` 左侧的 `<tree>` 组件及其 flex 双栏布局容器
- 清理 `user/utils/hook.tsx` 中与部门树相关的状态、方法、API 调用
- 页面改为单栏全宽布局：搜索表单 + 数据表格占据 100% 宽度
- 保留 `higherDeptOptions` 数据加载（用于新增/编辑用户的上级部门选择器）
- 保持所有 CRUD 功能不受影响

### 需求二：菜单管理页移除权限功能（功能删减+展示精简）

- 菜单树过滤掉 `menuType === 2` 的权限叶子节点（如 user:view、role:manage 等），仅显示目录(0)和页面(1)
- 表格列移除「权限标识」列
- 表单移除菜单类型中"权限"选项及对应的 HTTP 方法选择器字段
- 后端 API 不变，仅前端做展示层过滤

### 需求三：字典管理页完善新增字典功能（交互增强，参照 PureAdmin 截图）

参考截图显示：左侧面板底部有蓝色全宽「新增字典」按钮，树节点右键菜单应包含完整操作。

当前项目已有：

- 左下角「新增子典」按钮 — 创建根级字典类型
- 右上角「新增字典详情」按钮 — 创建选中类型下的子项

需补充：

- 左侧树节点的右键下拉菜单中增加第三个选项「新增子项」（icon=AddFill）
- 点击后以当前选中的字典类型为父节点打开新增对话框
- `hook.tsx` 扩展 `openAddDictDetail` 方法支持接收可选的父节点参数

### 需求四：后端操作日志排除 refresh-token 等接口（减少无效记录）

**问题**：当前 `RequestLoggingMiddleware` 对所有非 GET 请求无差别写入 `sys_logs` 审计表，导致：

- `POST /api/system/refresh-token` 每 30 分钟触发一次，产生大量无效日志且 body 含 refreshToken 明文
- `POST /api/system/login` body 含密码明文（已有独立 login_logs 表）
- 其他高频辅助接口（role-menu、list-role-ids 等）同样产生无业务审计价值的数据

**方案**：在中间件中增加 `_SKIP_LOG_PATH_PREFIXES` 前缀排除集合（frozenset），对匹配路径跳过数据库审计表写入。注意 access.log 文件日志仍保留，仅跳过 sys_logs 数据库写入。

## Tech Stack

### 前端部分

- **框架**: Vue 3 + TypeScript + Composition API（Pure Admin 模板）
- **UI**: Element Plus + PureAdmin 封装组件（RePureTableBar, pure-table, ReDialog, ReSegmented, ReCol）
- **样式**: Tailwind CSS + SCSS Scoped

### 后端部分

- **框架**: FastAPI (Python 3.10) + DDD 分层架构
- **中间件**: Starlette BaseHTTPMiddleware
- **ORM**: SQLModel + SQLAlchemy AsyncSession
- **日志**: loguru（access.log 文件 + app.log + error.log）

## 实现方案

### 一、用户管理页 -- 移除部门树（移除+清理策略）

**index.vue 修改要点**:

- 删除 `import tree from "./tree.vue"` (第3行)
- 删除 `const treeRef = ref()` (第21行)
- 外层 `<div class="flex justify-between ...">` (第54行) 改为普通 `<div>`
- 删除 `<tree>` 组件标签块 (第55-61行)
- 右侧内容区容器去除宽度约束 class：原 `w-[calc(100%-200px)]` (第63行) 改为 `w-full`
- 搜索表单的 `pl-8` 可调整为 `pl-4` 以匹配全宽布局
- `useUser(tableRef, treeRef)` (第50行) 改为 `useUser(tableRef)`

**hook.tsx 修改要点**:

- 函数签名从 `useUser(tableRef: Ref, treeRef: Ref)` (第41行) 改为 `useUser(tableRef: Ref)`
- 删除变量：`treeData`(第30行)、`treeLoading`(第31行)
- 删除方法：`onTreeSelect`(第40行)
- `resetForm` 中删除 `treeRef.value.onTreeReset()` 调用 (原第342行附近)
- `onMounted` 中保留 `deptApi.list() -> higherDeptOptions`，删除 `-> treeData` 赋值行 (原第576行附近)
- return 对象移除 treeData、treeLoading、onTreeSelect 导出 (第289-291行)

### 二、菜单管理页 -- 移除权限功能（过滤+精简策略）

**tree.vue 修改要点**:

- 在 el-tree 的 `#default` slot 模板中对 `data.menuType === 2` 的节点不渲染或使用 computed 过滤
- 推荐方案：用 computed 属性 `filteredTreeData` 过滤 props.treeData 中 menuType !== 2 的节点传给 el-tree
- 移除 el-tag 中"权限"(info) 类型的渲染分支 (原第99-115行)

**hook.tsx 修改要点**:

- columns 数组删除 `{ label: "权限标识", prop: "method", ... }` 整个对象 (第67-71行)
- openDialog 的 payload 对象中移除 `method` 字段 (第163行)；formInline 默认值中移除 method (原第163行)

**form.vue 修改要点**:

- menuTypeOptions import 中移除 `{ label: "权限", value: 2 }` 选项 (enums.ts 第13-16行)，或直接在 form.vue 的 Segmented :options 中只传前两项
- 删除请求方法选择器代码块 (`v-if="newFormInline.menuType === 2"` 的 re-col 块，原第157-170行)
- 删除 `methodOptions` import (如已导入)
- currentFormRules computed 中 case 2 分支可合并到 default

**edit.vue 修改要点**:

- 同 form.vue：移除权限选项、HTTP 方法字段、permissionFormRules 引用、methodOptions import

**enums.ts / rule.ts 修改要点**:

- enums.ts: methodOptions 可保留导出但标记注释说明不再被菜单模块使用
- rule.ts: permissionFormRules 可保留但不再引用

### 三、字典管理页 -- 完善新增功能（增强交互策略）

**index.vue 修改要点**:

- 在树节点的 `<el-dropdown-menu>` (第124-149行) 中，于现有「修改」「删除」两个 dropdown-item 之后，新增第三个 `<el-dropdown-item>`
- 新增内容：「新增子项」按钮，使用 AddFill 图标，type="primary"，点击事件传入当前节点 data 并调用新的 `openAddDictDetailForNode(data)` 方法

**hook.tsx 修改要点**:

- 新增方法 `openAddDictDetailForNode(parentNode?: any)`：
- 设置 `selectedDictType.value = parentNode`（自动选中该父节点并切换右侧数据）
- 复用现有 openAddDictDetail 的核心逻辑，以 parentNode.id 为 parentId 打开新增对话框
- 或者更简洁地：扩展 openAddDictDetail 使其接受可选参数 `parentNode?: any`，当传入时自动设置 selectedDictType
- return 对象增加导出此新方法

### 四、后端操作日志 -- 路径排除机制（配置化跳过策略）

**request_logging_middleware.py 修改要点**:

在模块级别（类定义之前）定义 `_SKIP_LOG_PATH_PREFIXES` 常量：

```python
# 不需要写入 SystemLog 审计表的路径前缀集合
# 这些路径仍会写入 access.log 文件，但不写数据库审计表
_SKIP_LOG_PATH_PREFIXES = frozenset({
    "/api/system/login",          # 含密码明文，有独立的 login_logs 表
    "/api/system/register",       # 含密码明文
    "/api/system/logout",         # 无业务审计价值
    "/api/system/refresh-token", # 高频(30min)、含敏感token
    "/api/system/get-async-routes",  # 高频路由加载
    "/api/system/list-all-role",    # 高频下拉列表
    "/api/system/list-role-ids",   # 高频角色查询
    "/api/system/role-menu",        # 高频权限查询
    "/api/system/role-menu-ids",   # 高频权限查询
})
```

添加静态方法 `_should_skip_log(path: str) -> bool` 用于前缀匹配判断。

修改 `dispatch()` 第111行判断条件：

```python
# 原: if request.method != "GET":
# 新:
if request.method != "GET" and not self._should_skip_log(request.url.path):
```

**设计决策**：

- 使用前缀匹配（非精确匹配），因为 role-menu-ids 与 role-menu 有相同前缀都能覆盖
- 使用 frozenset 保证 O(1) 查找性能和不可变性
- 仅影响 _write_system_log_async 调用，不影响 logger.debug、log_request(access.log)、X-Process-Time header
- 中文注释标注每个排除路径的原因

## 目录结构

```
web/src/views/system/
├── user/
│   ├── index.vue              # [MODIFY] 移除 tree 组件及左栏布局 → 全宽单栏
│   ├── utils/hook.tsx         # [MODIFY] 移除 treeRef 及全部树相关逻辑
│   └── tree.vue               # [UNCHANGED]
├── menu/
│   ├── index.vue              # [MINOR] 无需改动
│   ├── components/
│   │   ├── tree.vue           # [MODIFY] 过滤 menuType===2 权限节点
│   │   └── edit.vue           # [MODIFY] 移除权限选项和 HTTP 方法字段
│   ├── form.vue               # [MODIFY] 移除权限类型选项和 HTTP 方法选择器
│   └── utils/
│       ├── hook.tsx           # [MODIFY] 移除权限标识列和 method 字段
│       ├── enums.ts           # [MODIFY] 移除/注释 methodOptions
│       └── rule.ts            # [MODIFY] permissionFormRules 标记弃用
├── dictionary/
│   ├── index.vue              # [MODIFY] 树节点 dropdown 增加"新增子项"
│   ├── form.vue               # [UNCHANGED]
│   └── utils/hook.tsx         # [MODIFY] 新增 openAddDictDetailForNode 方法
service/src/infrastructure/http/
└── request_logging_middleware.py  # [MODIFY] 增加 _SKIP_LOG_PATH_PREFIXES 排除机制
```

四项优化均为局部页面改造或后端逻辑调整，非全新视觉设计。核心变化：

1. **用户管理页**: Flex 双栏 → 单栏全宽，消除左侧空树面板
2. **菜单管理页**: 仅保留目录+页面两种 tag，彻底移除权限叶子节点及相关表单字段
3. **字典管理页**: 左侧树右键菜单从 2 项操作扩充至 3 项（+新增子项），参照 PureAdmin 截图的交互模式
4. **后端中间件**: 纯逻辑修改，无 UI 变化

整体遵循 PureAdmin 框架现有的设计语言和组件规范，保持与项目其他页面的一致性。

## Skill

- **frontend-dev**
- Purpose: 执行前三项前端页面修改（用户管理移除部门树、菜单管理移除权限功能、字典管理完善新增交互），遵循 Pure Admin + Element Plus + Tailwind CSS 规范
- Expected outcome: 产出符合项目规范的前端代码改动

### Skill

- **python-code-quality**
- Purpose: 执行第四项后端操作日志中间件的路径排除机制修改，编写高质量 Python 代码，使用类型注解和中文注释
- Expected outcome: 产出符合项目 DDD 架构规范的中间件改动，含完善的路径排除逻辑和注释文档