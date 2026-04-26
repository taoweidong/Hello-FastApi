# 项目配置 - 通用 CRUD 生成器

> 本文件是项目特定的配置。适配新项目时，只需修改本文件和 `backend-patterns.md`、`frontend-patterns.md` 中的代码模板。

## 框架选择

必须先指定项目使用的框架类型：

```yaml
backend_framework: fastapi  # django 或 fastapi
frontend_framework: pure-admin  # pure-admin
```

---

## FastAPI + DDD 四层架构配置

### 目录结构约定

```
项目根目录/
├── service/                           # 后端根目录（FastAPI + DDD）
│   └── src/
│       ├── api/
│       │   └── v1/
│       │       └── {table}_router.py  # API 路由
│       ├── application/
│       │   ├── dto/
│       │   │   └── {table}_dto.py    # DTO
│       │   └── services/
│       │       └── {table}_service.py # 应用服务
│       ├── domain/
│       │   ├── entities/
│       │   │   └── {table}.py        # 领域实体
│       │   └── repositories/
│       │       └── {table}_repository.py  # 仓储接口
│       └── infrastructure/
│           ├── database/
│           │   └── models/
│           │       └── {table}.py    # ORM 模型
│           └── repositories/
│               └── {table}_repository.py # 仓储实现
└── web/                               # 前端根目录
    └── src/
        └── views/
            └── {app}/
                └── {table}/
                    ├── index.vue
                    └── utils/
                        ├── api.ts
                        └── hook.tsx
```

### 后端基类和导入路径（FastAPI）

| 组件 | 导入路径 | 说明 |
|------|---------|------|
| SQLModel | `from sqlmodel import Field, SQLModel` | ORM 基类 |
| Field | `from sqlmodel import Field` | 字段定义 |
| relationship | `from sqlmodel import Relationship` | 关联关系 |
| Router | `from classy_fastapi import Routable, get, post, put, delete` | 路由 |
| BaseRepository | `from src.infrastructure.repositories import BaseRepository` | 仓储基类 |

### 领域实体基类字段（需跳过）

| 字段名 | 来源 | 说明 |
|--------|------|------|
| id | BaseEntity | UUID 主键 |
| created_time | BaseEntity | 创建时间 |
| updated_time | BaseEntity | 更新时间 |

---

## Django REST Framework 配置

### 目录结构约定

```
项目根目录/
├── xadmin-server/                    # 后端根目录（Django）
│   ├── {app}/
│   │   ├── models/
│   │   │   └── {table}.py
│   │   ├── serializers/
│   │   │   └── {table}.py
│   │   ├── views/
│   │   │   └── {table}.py
│   │   └── urls.py
└── xadmin-client/                    # 前端根目录
    └── src/
        └── views/
            └── {app}/
                └── {table}/
```

### 后端基类（Django）

| 组件 | 导入路径 | 说明 |
|------|---------|------|
| DbAuditModel | `from common.core.models import DbAuditModel` | 审计模型基类 |
| BaseModelSerializer | `from common.core.serializers import BaseModelSerializer` | Serializer 基类 |
| BaseModelSet | `from common.core.modelset import BaseModelSet` | ViewSet 基类 |
| BaseFilterSet | `from common.core.filter import BaseFilterSet` | Filter 基类 |

---

## 前端配置（pure-admin）

### API 基类

| 组件 | 导入路径 |
|------|---------|
| BaseApi | `import { BaseApi } from "@/api/base"` |

### 页面组件

| 组件 | 说明 |
|------|------|
| RePlusPage | CRUD 页面组件，自动渲染表格/搜索/表单 |

### 命名规则

| 概念 | 规则 | 示例 |
|------|------|------|
| API 类名 | PascalCase + Api | `BookApi` |
| API 实例名 | camelCase + Api | `bookApi` |
| Vue 组件 name | PascalCase | `DemoBook` |
| locale-name | camelCase | `demoBook` |
| Hook 函数名 | use + PascalCase | `useDemoBook` |

---

## URL 和路由约定

### FastAPI 路由

- 路由前缀：`/api/system/{table}`（API 前缀 + 模块名）
- Router 注册：使用 `APIRouter` 添加子路由

### Django 路由

- 路由前缀：`/api/{app}/{table}`
- 使用 `SimpleRouter(False)` 注册 ViewSet