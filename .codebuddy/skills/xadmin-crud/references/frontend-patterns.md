# 前端代码模式参考

本文档包含 xadmin-client 项目的前端代码模式，生成代码时必须严格遵循这些模式。

## 1. 前端文件结构

每个数据表对应以下文件：

```
xadmin-client/src/
├── api/{app_name}/
│   └── {table_name}.ts               # API 类
├── views/{app_name}/{table_name}/
│   ├── index.vue                      # 页面组件
│   └── utils/
│       ├── hook.tsx                   # Hook 逻辑
│       └── api.ts                     # API 实例（可选）
```

## 2. API 类模式

### 2.1 标准 API 类（无自定义接口）

```typescript
import { BaseApi } from "@/api/base";

class {ModelName}Api extends BaseApi {}

export const {modelNameLower}Api = new {ModelName}Api("/api/{app_name}/{url_path}");
```

### 2.2 带自定义接口的 API 类

当后端 ViewSet 有自定义 `@action` 装饰器的接口时，需要在 API 类中添加对应方法：

```typescript
import { BaseApi } from "@/api/base";
import type { BaseResult } from "@/api/types";

class {ModelName}Api extends BaseApi {
  // 自定义 action 接口
  {actionName} = (pk: number | string, data?: object) => {
    return this.request<BaseResult>(
      "post",          // HTTP 方法
      {},              // params
      data,            // request body
      `${this.baseApi}/${pk}/{action_url}`  // 自定义 URL
    );
  };
}

export const {modelNameLower}Api = new {ModelName}Api("/api/{app_name}/{url_path}");
```

### 2.3 BaseApi 已有方法

以下方法由 `BaseApi` 基类提供，无需重复定义：

| 方法 | HTTP | 路径 | 说明 |
|---|---|---|---|
| `choices()` | GET | `/choices` | 获取字段选项 |
| `fields(params?)` | GET | `/search-fields` | 获取搜索字段 |
| `columns(params?)` | GET | `/search-columns` | 获取展示字段 |
| `list(params?)` | GET | `/` | 获取列表 |
| `create(data?)` | POST | `/` | 创建 |
| `retrieve(pk, params?)` | GET | `/${pk}` | 获取详情 |
| `update(pk, data?)` | PUT | `/${pk}` | 整体更新 |
| `partialUpdate(pk, data?)` | PATCH | `/${pk}` | 部分更新 |
| `destroy(pk, params?)` | DELETE | `/${pk}` | 删除 |
| `batchDestroy(pks)` | POST | `/batch-destroy` | 批量删除 |
| `exportData(params)` | GET | `/export-data` | 导出数据 |
| `importData(params, data)` | POST | `/import-data` | 导入数据 |

### 2.4 API 实例命名规则

- 类名：PascalCase，如 `BookApi`、`DeptApi`
- 实例名：camelCase，如 `bookApi`、`deptApi`
- 路径格式：`/api/{app_name}/{url_path}`，其中 `url_path` 为表名的 kebab-case 形式

## 3. Vue 页面组件模式

### 3.1 标准页面组件

```vue
<script lang="ts" setup>
import { use{ModelName} } from "./utils/hook";
import { ref } from "vue";

defineOptions({
  name: "{RouteName}" // 必须定义，用于菜单自动匹配组件
});

const tableRef = ref();

const {
  api,
  auth,
  listColumnsFormat
} = use{ModelName}(tableRef);
</script>

<template>
  <RePlusPage
    ref="tableRef"
    :api="api"
    :auth="auth"
    locale-name="{localeName}"
    :list-columns-format="listColumnsFormat"
  />
</template>
```

### 3.2 defineOptions 的 name 规则

- 格式：PascalCase，如 `DemoBook`、`SystemDept`
- 通常为：`{AppName}{TableName}` 的 PascalCase 组合
- 这个 name **必须**与后端菜单配置中的组件名一致

### 3.3 locale-name 规则

- 格式：camelCase，如 `demoBook`、`systemDept`
- 规则：app 名首字母小写 + 表名 PascalCase
- 例如：`demo` + `book` → `demoBook`
- 例如：`system` + `dept` → `systemDept`
- 例如：`order` + `order-item` → `orderOrderItem`

### 3.4 RePlusPage 常用 Props

| Prop | 类型 | 说明 |
|---|---|---|
| `api` | `BaseApi` | API 实例（必须） |
| `auth` | `object` | 权限控制（必须） |
| `locale-name` | `string` | i18n 前缀（必须） |
| `isTree` | `boolean` | 是否树形表格 |
| `listColumnsFormat` | `function` | 列渲染格式化 |
| `searchColumnsFormat` | `function` | 搜索表单格式化 |
| `addOrEditOptions` | `object` | 新增/编辑对话框配置 |
| `operationButtonsProps` | `object` | 操作按钮配置 |
| `tableBarButtonsProps` | `object` | 表格标题栏按钮配置 |

## 4. Hook 逻辑模式

### 4.1 标准 Hook（最小化版本）

对于简单的 CRUD 页面，只需生成最基本的 hook：

```typescript
import { {modelNameLower}Api } from "@/api/{app_name}/{table_name}";
import { getCurrentInstance, reactive, type Ref } from "vue";
import { getDefaultAuths } from "@/router/utils";

export function use{ModelName}(tableRef: Ref) {
  const api = reactive({modelNameLower}Api);

  const auth = reactive({
    ...getDefaultAuths(getCurrentInstance())
  });

  const listColumnsFormat = (columns: any[]) => {
    // 自定义列渲染逻辑
    return columns;
  };

  return {
    api,
    auth,
    listColumnsFormat
  };
}
```

### 4.2 带自定义操作按钮的 Hook

当后端 ViewSet 有自定义 `@action` 时，需要在 hook 中添加对应按钮：

```typescript
import { {modelNameLower}Api } from "@/api/{app_name}/{table_name}";
import { getCurrentInstance, reactive, type Ref, shallowRef } from "vue";
import { getDefaultAuths } from "@/router/utils";
import type { OperationProps, PageTableColumn } from "@/components/RePlusPage";
import { handleOperation } from "@/components/RePlusPage";
import { useI18n } from "vue-i18n";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import {IconName} from "~icons/{icon_path}";

export function use{ModelName}(tableRef: Ref) {
  const api = reactive({modelNameLower}Api);
  const auth = reactive({
    {actionName}: false,
    ...getDefaultAuths(getCurrentInstance(), ["{actionName}"])
  });
  const { t } = useI18n();

  // 操作按钮配置
  const operationButtonsProps = shallowRef<OperationProps>({
    width: 200,
    buttons: [
      {
        text: t("{localeName}.{actionName}"),
        code: "{actionName}",
        confirm: {
          title: (row: any) => {
            return t("{localeName}.confirm{ActionName}", { name: row.{display_field} });
          }
        },
        props: {
          type: "primary",
          icon: useRenderIcon({IconName}),
          link: true
        },
        onClick: ({ row, loading }: any) => {
          loading.value = true;
          handleOperation({
            t,
            apiReq: api.{actionName}(row?.pk ?? row?.id),
            success() {
              tableRef.value.handleGetData();
            },
            requestEnd() {
              loading.value = false;
            }
          });
        },
        show: auth.{actionName}
      }
    ]
  });

  const listColumnsFormat = (columns: PageTableColumn[]) => {
    return columns;
  };

  return {
    api,
    auth,
    listColumnsFormat,
    operationButtonsProps
  };
}
```

### 4.3 带 addOrEditOptions 的 Hook

当新增/编辑表单需要自定义字段渲染时：

```typescript
import { shallowRef, type Ref } from "vue";
import type { RePlusPageProps } from "@/components/RePlusPage";

export function use{ModelName}(tableRef: Ref) {
  // ...

  const addOrEditOptions = shallowRef<RePlusPageProps["addOrEditOptions"]>({
    props: {
      columns: {
        // 自定义字段渲染
        {field_name}: ({ column }) => {
          // 修改 column 的 valueType, fieldProps 等
          return column;
        }
      }
    }
  });

  return {
    api,
    auth,
    listColumnsFormat,
    addOrEditOptions
  };
}
```

### 4.4 树形表格的 Hook（自关联表）

当表有 parent 自关联字段时，使用树形表格：

```typescript
export function use{ModelName}(tableRef: Ref) {
  // ...

  const addOrEditOptions = shallowRef<RePlusPageProps["addOrEditOptions"]>({
    props: {
      row: {
        parent: ({ rawRow }) => {
          return rawRow?.parent?.pk ?? "";
        }
      },
      columns: {
        parent: ({ column }) => {
          column["valueType"] = "cascader";
          column["fieldProps"] = {
            ...column["fieldProps"],
            ...{
              props: {
                value: "pk",
                label: "name",
                emitPath: false,
                checkStrictly: true
              }
            }
          };
          return column;
        }
      }
    }
  });

  return {
    api,
    auth,
    listColumnsFormat,
    addOrEditOptions
  };
}
```

对应 Vue 页面需要添加 `isTree` prop：

```vue
<RePlusPage
  ref="tableRef"
  :api="api"
  :auth="auth"
  :isTree="true"
  locale-name="{localeName}"
  :addOrEditOptions="addOrEditOptions"
  :listColumnsFormat="listColumnsFormat"
/>
```

## 5. 独立 API 实例文件（可选）

当 API 类有自定义接口时，建议将 API 实例单独放在 `utils/api.ts` 中，hook 中导入使用。

### 5.1 utils/api.ts

```typescript
import { BaseApi } from "@/api/base";
import type { BaseResult } from "@/api/types";

class {ModelName}Api extends BaseApi {
  {actionName} = (pk: number | string) => {
    return this.request<BaseResult>(
      "post",
      {},
      {},
      `${this.baseApi}/${pk}/{action_url}`
    );
  };
}

const {modelNameLower}Api = new {ModelName}Api("/api/{app_name}/{url_path}");
export { {modelNameLower}Api };
```

### 5.2 何时使用独立 API 文件

- **简单 CRUD（无自定义接口）**：直接在 `src/api/{app}/` 下创建 API 文件，hook 中导入
- **有自定义接口**：在 `utils/api.ts` 中定义 API 类（包含自定义方法），hook 中导入

## 6. 前端导入语句汇总

```typescript
// API 文件
import { BaseApi } from "@/api/base";
import type { BaseResult, DetailResult, ListResult } from "@/api/types";

// Hook 文件
import { {apiInstanceName} } from "@/api/{app_name}/{table_name}";  // 或 from "./api"
import { getCurrentInstance, reactive, ref, type Ref, shallowRef } from "vue";
import { getDefaultAuths } from "@/router/utils";
import { useI18n } from "vue-i18n";
import { handleTree } from "@/utils/tree";  // 树形表格需要
import {
  type PageTableColumn,
  type PageColumn,
  type OperationProps,
  type RePlusPageProps,
  handleOperation,
  openDialogDrawer
} from "@/components/RePlusPage";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

// 图标
import {IconName} from "~icons/{icon_path}";
```

## 7. 生成规则总结

1. **最小化原则**：标准 CRUD 页面只生成 `api/{app}/{table}.ts`、`views/{app}/{table}/index.vue`、`views/{app}/{table}/utils/hook.tsx` 三个文件
2. **RePlusPage 自动渲染**：利用后端 `search-columns` 和 `search-fields` 接口，前端无需手动定义列和搜索表单
3. **有自定义 action 时**：API 类添加对应方法，hook 添加 `operationButtonsProps`
4. **有自关联字段时**：Vue 页面添加 `isTree` prop，hook 添加 `addOrEditOptions` 配置 parent 字段
5. **locale-name 命名**：app 名 + 表名驼峰化，如 `demoBook`
6. **defineOptions name**：PascalCase 格式，如 `DemoBook`
