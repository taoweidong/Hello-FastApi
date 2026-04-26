# 项目配置 - xadmin

> 本文件是项目特定的配置。适配新项目时，只需修改本文件和 `backend-patterns.md`、`frontend-patterns.md` 中的代码模板。

## 目录结构约定

```
项目根目录/
├── xadmin-server/                  # 后端根目录
│   ├── {app}/                      # Django app 目录
│   │   ├── models/
│   │   │   ├── __init__.py         # from .xxx import *
│   │   │   └── {表名}.py           # 每个模型一个文件
│   │   ├── serializers/
│   │   │   ├── __init__.py
│   │   │   └── {表名}.py
│   │   ├── views/
│   │   │   └── {表名}.py           # ViewSet + FilterSet
│   │   ├── urls.py
│   │   ├── apps.py
│   │   ├── config.py               # URLPATTERNS 路由注入
│   │   └── __init__.py
│   └── server/settings.py          # INSTALLED_APPS 注册
└── xadmin-client/                  # 前端根目录
    └── src/
        └── views/
            └── {app}/
                └── {表名}/
                    ├── index.vue
                    └── utils/
                        ├── api.ts
                        └── hook.tsx
```

## 后端基类和导入路径

### Model 基类

| 基类名 | 导入路径 | 用途 |
|--------|---------|------|
| `DbAuditModel` | `from common.core.models import DbAuditModel` | 默认基类，含审计字段 |
| `AutoCleanFileMixin` | `from common.core.models import AutoCleanFileMixin` | 有文件字段时混入 |
| `upload_directory_path` | `from common.core.models import upload_directory_path` | 文件上传路径函数 |

### Model 基类已有字段（需跳过）

| 字段名 | 来源基类 | 说明 |
|--------|---------|------|
| `id` | `DbUuidModel` | UUID 主键 |
| `created_time` | `DbBaseModel` | auto_now_add |
| `updated_time` | `DbBaseModel` | auto_now |
| `description` | `DbBaseModel` | 描述 |
| `creator` | `DbAuditModel` | 创建人 FK |
| `modifier` | `DbAuditModel` | 修改人 FK |
| `dept_belong` | `DbAuditModel` | 数据归属部门 FK |

### Serializer 基类

| 基类名 | 导入路径 | 用途 |
|--------|---------|------|
| `BaseModelSerializer` | `from common.core.serializers import BaseModelSerializer` | 默认基类 |
| `TabsColumn` | `from common.core.serializers import TabsColumn` | tabs 表单分组 |

### ViewSet 基类

| 基类名 | 导入路径 | 用途 |
|--------|---------|------|
| `BaseModelSet` | `from common.core.modelset import BaseModelSet` | 完整 CRUD ViewSet |
| `ImportExportDataAction` | `from common.core.modelset import ImportExportDataAction` | 导入导出 Mixin |

### Filter 基类

| 基类名 | 导入路径 | 用途 |
|--------|---------|------|
| `BaseFilterSet` | `from common.core.filter import BaseFilterSet` | 默认 FilterSet 基类 |
| `PkMultipleFilter` | `from common.core.filter import PkMultipleFilter` | 关联字段多选过滤器 |

### 其他导入

| 名称 | 导入路径 | 用途 |
|------|---------|------|
| `DynamicPageNumber` | `from common.core.pagination import DynamicPageNumber` | 自定义分页 |
| `get_logger` | `from common.utils import get_logger` | 日志 |
| `SimpleRouter` | `from rest_framework.routers import SimpleRouter` | 路由注册 |

### 系统内置模型（ForeignKey 常用引用）

| 模型 | 导入路径 |
|------|---------|
| `UserInfo` | `from system.models import UserInfo` |
| `DeptInfo` | `from system.models import DeptInfo` |
| `UploadFile` | `from system.models import UploadFile` |

## ForeignKey extra_kwargs 规则

```python
# ForeignKey 字段在 Serializer 的 extra_kwargs 配置
'字段名': {
    'attrs': ['pk', '关联模型可读字段'],  # pk 必须有，加一个可读字段用于展示
    'required': True/False,                # 根据 DDL NOT NULL 判断
    'format': "{可读字段名}({pk})",         # 前端显示格式
}
# 若关联数据量大，添加 'input_type': 'api-search-user' 等
# 若关联 UploadFile，添加 'ignore_field_permission': True
```

## URL 和路由约定

- 路由器：`SimpleRouter(False)` —— False 去掉 URL 尾部斜线
- 注册格式：`router.register(路由前缀, ViewSet, basename=路由前缀)`
- API 路径模式：`/api/{app名}/{路由前缀}`
- App 路由注入：在 `config.py` 的 `URLPATTERNS` 中配置 `path('api/{app}/', include('{app}.urls'))`

## App 初始化模板

新 app 需创建的文件（参考 `backend-patterns.md` 中的完整代码）：

| 文件 | 说明 |
|------|------|
| `__init__.py` | 空文件 |
| `apps.py` | AppConfig 类，name = app 名 |
| `config.py` | URLPATTERNS 路由注入 + PERMISSION_WHITE_REURL |
| `urls.py` | SimpleRouter + register |
| `admin.py` | 空文件 |
| `models/__init__.py` | 空文件 |
| `serializers/__init__.py` | 空文件 |
| `migrations/__init__.py` | 空文件 |

## 前端基类和组件

### API 基类

| 基类名 | 导入路径 | 用途 |
|--------|---------|------|
| `BaseApi` | `import { BaseApi } from "@/api/base"` | 默认 API 基类，已含 CRUD 方法 |

### 页面组件

| 组件名 | 导入路径 | 用途 |
|--------|---------|------|
| `RePlusPage` | 自动全局注册 | CRUD 页面组件，自动渲染表格/搜索/表单 |

### Hook 工具

| 函数名 | 导入路径 | 用途 |
|--------|---------|------|
| `getDefaultAuths` | `import { getDefaultAuths } from "@/router/utils"` | 获取按钮权限 |
| `reactive` | `import { reactive } from "vue"` | 响应式包装 |
| `shallowRef` | `import { shallowRef } from "vue"` | 浅响应式 |
| `useI18n` | `import { useI18n } from "vue-i18n"` | 国际化 |

## 前端命名规则

| 概念 | 规则 | 示例 |
|------|------|------|
| API 类名 | PascalCase + Api | `BookApi` |
| API 实例名 | camelCase + Api | `bookApi` |
| API 文件路径 | `src/views/{app}/{表名}/utils/api.ts` | |
| Vue 组件 name | PascalCase (App+Model) | `DemoBook`、`SystemDept` |
| locale-name | camelCase (app+Model) | `demoBook`、`systemDept` |
| Hook 函数名 | use + PascalCase(Model) | `useDemoBook` |
| Hook 文件路径 | `src/views/{app}/{表名}/utils/hook.tsx` | |
| Vue 文件路径 | `src/views/{app}/{表名}/index.vue` | |
