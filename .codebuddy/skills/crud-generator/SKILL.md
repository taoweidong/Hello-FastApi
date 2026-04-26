---
name: crud-generator
description: >
  通用的 CRUD 代码生成 Skill。从 MySQL/PostgreSQL 数据表 DDL 或表名，自动生成完整的后端 + 前端 CRUD 代码。
  支持多种后端框架（Django/FastAPI）和前端框架（pure-admin/Vue3）。
  触发关键词：数据表、CRUD、REST接口、生成代码、建表、DDL、数据库表、增删改查、代码生成。
---

# 通用 CRUD 代码生成 Skill

从数据库表 DDL 或表名，按项目模板自动生成完整的后端 + 前端 CRUD 代码。

> **适配新项目**：只需修改 `references/project-config.md` 中的配置即可，本文件无需改动。

## 支持的框架

| 类别 | 支持的框架 |
|------|-----------|
| 后端 | Django REST Framework, FastAPI |
| 前端 | pure-admin (Vue3 + Element Plus) |

---

## 第零步：加载项目配置

**开始任何步骤前，必须先加载 `references/project-config.md`**，获取以下项目特定配置：

- 目录结构约定（后端/前端根目录、文件组织方式）
- 后端框架类型（Django/FastAPI）及对应基类
- 前端框架类型及组件配置
- 基类已有字段（需要跳过不生成的字段列表）
- URL 和路由约定

---

## 第一步：解析输入

### 1.1 解析 DDL 语句

若用户提供 DDL 语句，提取：
- 表名、列定义、类型、约束、注释
- 外键关联关系
- 索引和唯一约束
- 枚举值定义

### 1.2 处理表名

若用户只指定表名：
- 询问字段信息
- 或从数据库读取表结构（需要数据库连接）
- 或使用默认常见字段类型

### 1.3 确定 App 名称

- 默认使用表名作为 app 名
- 支持自定义 app 名称
- 判断是追加到已有 app 还是创建新 app

---

## 第二步：后端代码生成

根据 `project-config.md` 中指定的框架类型，选择对应的生成策略。

### 2.1 Django REST Framework 模式

若框架为 Django，生成以下文件：

| 文件 | 说明 |
|------|------|
| `{app}/models/{table}.py` | Model 类 |
| `{app}/serializers/{table}.py` | Serializer 类 |
| `{app}/views/{table}.py` | ViewSet + FilterSet |
| `{app}/urls.py` | 路由注册 |

**加载参考**：`references/backend-patterns.md` → Django 模式

### 2.2 FastAPI 模式

若框架为 FastAPI + DDD，按四层架构生成：

| 层次 | 文件 | 说明 |
|------|------|------|
| domain | `domain/entities/{table}.py` | 领域实体 |
| domain | `domain/repositories/{table}_repository.py` | 仓储接口 |
| infrastructure | `infrastructure/database/models/{table}.py` | ORM 模型 |
| infrastructure | `infrastructure/repositories/{table}_repository.py` | 仓储实现 |
| application | `application/dto/{table}_dto.py` | DTO 定义 |
| application | `application/services/{table}_service.py` | 应用服务 |
| api | `api/v1/{table}_router.py` | API 路由 |

**加载参考**：`references/backend-patterns.md` → FastAPI 模式

### 2.3 模型字段处理

- 跳过基类已有字段（见 project-config.md）
- MySQL 类型映射为框架字段类型（见 type-mapping.md）
- 字段注释映射为 verbose_name/description
- 外键自动添加 related_name
- 枚举字段生成 Choices 类

---

## 第三步：前端代码生成

根据 `project-config.md` 中指定的前端框架类型，选择对应的生成策略。

### 3.1 pure-admin 模式

生成以下文件：

| 文件 | 说明 |
|------|------|
| `src/api/{app}/{table}.ts` | API 类 |
| `src/views/{app}/{table}/index.vue` | 页面组件 |
| `src/views/{app}/{table}/utils/hook.tsx` | Hook 逻辑 |

**加载参考**：`references/frontend-patterns.md` → pure-admin 模式

### 3.2 页面配置

- 表格列配置（table_fields）
- 搜索表单配置（search_fields）
- 新增/编辑表单配置（tabs 分组）
- 树形表格支持（自关联表）

---

## 第四步：文件追加逻辑

### 4.1 追加到已有 App

| 层级 | 操作 |
|------|------|
| Model | 创建文件 → `__init__.py` 追加 import |
| Serializer | 创建文件 → `__init__.py` 追加 import |
| ViewSet/Router | 创建文件 → 路由注册追加 |
| 前端 API | 创建/追加文件 |
| 前端页面 | 创建目录和文件 |

### 4.2 创建新 App

除生成业务代码外，还需创建：
- 应用配置文件
- 路由入口文件
- `__init__.py`

---

## 命名规则

| 概念 | 规则 | 示例 |
|------|------|------|
| App 名 | snake_case | `book_management` |
| Model/Entity 类名 | PascalCase | `BookInfo` |
| 文件名 | snake_case | `book_info.py` |
| Serializer 类名 | PascalCase + Serializer | `BookInfoSerializer` |
| ViewSet 类名 | PascalCase + ViewSet | `BookInfoViewSet` |
| Router 类名 | PascalCase + Router | `BookInfoRouter` |
| 路由前缀 | kebab-case | `book-info` |
| 前端 API 类名 | PascalCase + Api | `BookApi` |
| 前端 API 实例 | camelCase + Api | `bookApi` |
| 页面组件 name | PascalCase | `BookInfo` |
| locale-name | camelCase | `bookInfo` |
| Hook 函数名 | use + PascalCase | `useBookInfo` |

---

## 决策树

```
用户输入（DDL 或 表名）
├── 解析输入
│   ├── DDL → 提取表结构
│   └── 表名 → 询问/读取字段
├── 确定目标 App
│   ├── 已有 app → 追加模式
│   └── 新建 app → 创建完整结构
├── 选择后端框架
│   ├── Django → DRF 模式
│   └── FastAPI → DDD 四层模式
├── 生成后端代码
│   ├── Model/Entity
│   ├── Repository (接口 + 实现)
│   ├── DTO
│   ├── Service
│   └── Router
└── 生成前端代码
    ├── API 类
    ├── Vue 页面
    └── Hook 逻辑
```