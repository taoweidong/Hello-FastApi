# 前端代码模式参考

本文档包含前端代码生成模板。适配新项目时，根据 `project-config.md` 中指定的前端框架选择对应的模式。

---

## 1. pure-admin (Vue3 + Element Plus) 模式

### 1.1 API 类文件（src/api/{app}/{table}.ts）

```typescript
import { BaseApi } from "@/api/base";

class {ModelName}Api extends BaseApi {}

export const {modelNameLower}Api = new {ModelName}Api("/api/{app}/{url_path}");
```

**BaseApi 已有方法**：

| 方法 | HTTP | 路径 |
|------|------|------|
| `list(params?)` | GET | `/` |
| `create(data)` | POST | `/` |
| `retrieve(pk)` | GET | `/${pk}` |
| `update(pk, data)` | PUT | `/${pk}` |
| `partialUpdate(pk, data)` | PATCH | `/${pk}` |
| `destroy(pk)` | DELETE | `/${pk}` |
| `batchDestroy(pks)` | POST | `/batch-destroy` |
| `choices()` | GET | `/choices` |

### 1.2 页面组件（src/views/{app}/{table}/index.vue）

```vue
<script lang="ts" setup>
import { use{ModelName} } from "./utils/hook";
import { ref } from "vue";

defineOptions({
  name: "{AppName}{ModelName}"  // 必须，用于菜单匹配
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

### 1.3 Hook 逻辑（src/views/{app}/{table}/utils/hook.tsx）

```typescript
import { {modelNameLower}Api } from "@/api/{app}/{table}";
import { getCurrentInstance, reactive, type Ref } from "vue";
import { getDefaultAuths } from "@/router/utils";

export function use{ModelName}(tableRef: Ref) {
  const api = reactive({modelNameLower}Api);

  const auth = reactive({
    ...getDefaultAuths(getCurrentInstance())
  });

  const listColumnsFormat = (columns: any[]) => {
    // 自定义列渲染
    return columns;
  };

  return {
    api,
    auth,
    listColumnsFormat
  };
}
```

### 1.4 命名规则

| 概念 | 规则 | 示例 |
|------|------|------|
| API 类名 | PascalCase + Api | `BookApi` |
| API 实例名 | camelCase + Api | `bookApi` |
| Vue name | PascalCase | `DemoBook` |
| locale-name | camelCase | `demoBook` |
| Hook 函数 | use + PascalCase | `useDemoBook` |

### 1.5 自定义 action 扩展

当后端有自定义接口时，扩展 API 类：

```typescript
class {ModelName}Api extends BaseApi {
  // 自定义 action
  customAction = (pk: number | string, data?: object) => {
    return this.request(
      "post",
      {},
      data,
      `${this.baseApi}/${pk}/custom-action`
    );
  };
}
```

对应在 Hook 中添加操作按钮：

```typescript
const operationButtonsProps = shallowRef({
  buttons: [{
    text: t("{localeName}.customAction"),
    code: "customAction",
    onClick: ({ row }) => api.customAction(row.pk)
  }]
});
```

### 1.6 树形表格支持

对于自关联表（parent_id）：

```typescript
const addOrEditOptions = shallowRef({
  props: {
    row: {
      parent: ({ rawRow }) => rawRow?.parent?.pk ?? ""
    },
    columns: {
      parent: ({ column }) => {
        column.valueType = "cascader";
        return column;
      }
    }
  }
});
```

Vue 页面添加 `isTree` prop：

```vue
<RePlusPage :isTree="true" ... />
```