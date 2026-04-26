---
name: xadmin-crud
description: >
  从 MySQL 数据表 DDL 或表名自动生成完整的后端 + 前端 CRUD 代码。当用户需要从数据库表生成 REST 接口、
  生成 Model/Serializer/ViewSet 代码、生成前端页面、创建数据表的增删改查功能时触发。
  触发关键词：数据表、CRUD、REST接口、生成代码、建表、DDL、数据库表、增删改查。
---

# CRUD 代码生成 Skill

从 MySQL DDL 或表名，按项目模板自动生成后端 + 前端完整 CRUD 代码。

> **适配新项目**：只需修改 `references/project-config.md` 和 `references/backend-patterns.md`、`references/frontend-patterns.md` 中的代码模板即可，本文件无需改动。

## 第零步：加载项目配置

**开始任何步骤前，必须先加载 `references/project-config.md`**，获取以下项目特定配置：

- 目录结构约定（后端/前端根目录、文件组织方式）
- 基类名称和导入路径（Model 基类、Serializer 基类、ViewSet 基类、Filter 基类等）
- 基类已有字段（需要跳过不生成的字段列表）
- 前端组件名称和导入路径（API 基类、页面组件、Hook 模式等）
- URL 和路由约定
- App 配置文件模板

## 1. 解析输入

1. 若用户提供 DDL 语句：提取表名、列定义、类型、约束、注释
2. 若用户指定表名：询问或推断表结构（字段、类型等）
3. 确认目标 app 名称（默认使用表名作为 app 名）
4. 判断目标是追加到已有 app 还是创建新 app

**加载参考**：执行此步骤时加载 `references/type-mapping.md`

## 2. 后端代码生成（按顺序执行）

每一步都要参照 `project-config.md` 中的基类和导入路径，以及 `backend-patterns.md` 中的代码模板。

### 2.1 Model 文件

- 继承项目配置中的 Model 基类，自动跳过基类已有字段（见 project-config.md）
- 将 MySQL 类型映射为框架字段类型（见 type-mapping.md）
- 为每个字段添加 `verbose_name`（取自 MySQL COMMENT）
- 为有默认值的字段设置 `default`
- 设置 `Meta.verbose_name` 和 `Meta.verbose_name_plural`
- 添加 `__str__` 方法
- 若有 ForeignKey，自动添加 `related_name`（格式见 project-config.md）

**加载参考**：`references/backend-patterns.md` → Model 模式

### 2.2 Serializer 文件

- 继承项目配置中的 Serializer 基类
- `fields` 列表：`['pk']` + 所有非基类字段名
- `table_fields` 列表：选择表格中需要展示的字段
- `extra_kwargs`：`pk` 设为 `read_only=True`；关联字段添加 `attrs`/`format`/`required`
- 关联字段的 `attrs`/`format` 规则见 project-config.md

**加载参考**：`references/backend-patterns.md` → Serializer 模式

### 2.3 ViewSet + FilterSet 文件

- ViewSet 继承项目配置中的 ViewSet 基类 + 导入导出 Mixin
- FilterSet 继承项目配置中的 Filter 基类
- 字符串字段用 `icontains` 查询；关联字段用项目特定的多选过滤器
- ViewSet 必须写 docstring
- 设置 `queryset`、`serializer_class`、`ordering_fields`、`filterset_class`

**加载参考**：`references/backend-patterns.md` → ViewSet+FilterSet 模式

### 2.4 URL 路由文件

- 使用项目配置中的 Router 类注册 ViewSet
- 路由注册格式见 project-config.md

**加载参考**：`references/backend-patterns.md` → URL 模式

### 2.5 App 配置文件（仅新 app 时）

创建项目配置中规定的 App 必需文件：
- AppConfig 类文件
- 路由注入配置文件
- `__init__.py` 等

**加载参考**：`references/backend-patterns.md` → App 配置模式

## 3. 前端代码生成（按顺序执行）

每一步都要参照 `project-config.md` 中的前端组件和导入路径，以及 `frontend-patterns.md` 中的代码模板。

### 3.1 API 类文件

- 继承项目配置中的 API 基类
- 构造函数传入 API 路径
- 导出实例

**加载参考**：`references/frontend-patterns.md` → API 模式

### 3.2 页面组件

- 使用项目配置中的页面组件
- 组件名和 locale-name 命名规则见 project-config.md

**加载参考**：`references/frontend-patterns.md` → 页面组件模式

### 3.3 Hook/逻辑文件

- 使用项目配置中的 Hook 模式
- 初始化 api、auth 等

**加载参考**：`references/frontend-patterns.md` → Hook 模式

## 文件追加逻辑

### 已有 app 时追加代码

按照 `project-config.md` 中的目录约定，在对应位置创建新文件并追加 import：
1. Model：创建文件 → 在 `__init__.py` 追加 import
2. Serializer：创建文件 → 在 `__init__.py` 追加 import
3. ViewSet + FilterSet：创建文件
4. URL：追加 import 和 router.register
5. 前端：按目录约定创建文件

### 新建 app 时额外创建

按照 `project-config.md` 中的 App 初始化模板创建所有必需文件。

## 命名规则

| 概念 | 规则 | 示例 |
|------|------|------|
| App 名 | snake_case | `book_management` |
| Model 类名 | PascalCase | `BookInfo` |
| Model 文件名 | snake_case | `book_info.py` |
| Serializer 类名 | PascalCase + Suffix | 见 project-config.md |
| ViewSet 类名 | PascalCase + Suffix | 见 project-config.md |
| FilterSet 类名 | PascalCase + Suffix | 见 project-config.md |
| URL 路由前缀 | kebab-case | `book-info` |
| 前端 API 类名 | PascalCase + Suffix | 见 project-config.md |
| 前端 API 实例名 | camelCase + Suffix | 见 project-config.md |
| 页面组件 name | 见 project-config.md | |
| locale-name | 见 project-config.md | |
| Hook 函数名 | use + PascalCase | `useDemoBook` |

## 决策树

```
用户输入
├── 提供了 DDL？
│   ├── 是 → 解析 DDL 提取表结构
│   └── 否 → 询问字段信息或从数据库读取
├── 指定了目标 app？
│   ├── 是 → 检查 app 是否已存在
│   │   ├── 存在 → 追加模式
│   │   └── 不存在 → 创建新 app
│   └── 否 → 使用表名作为 app 名
├── 生成后端代码（Model → Serializer → ViewSet+Filter → URL → App配置）
└── 生成前端代码（API → 页面组件 → Hook）
```
