---
name: frontend-dev
description: >
  前端页面开发技能，遵循 Pure Admin 框架规范，使用项目封装的共享 Composables
  和 @pureadmin/utils 工具库，减少重复代码，统一样式和交互模式。
  当用户需要开发新前端页面、CRUD 管理模块、或前端组件时使用此技能。
  生成的代码使用 useCrudTable/useSwitchStatus/useDialogForm 共享逻辑，
  遵循 ReDialog + RePureTableBar + pure-table 的标准页面结构。
---

# 前端开发技能

## 概述

本技能提供前端页面开发的标准规范和代码模板，遵循 Pure Admin 框架约定（参照 vue-pure-admin 官方仓库示例），使用共享 Composables 消除重复代码，统一交互样式。

## 触发条件

当用户提出以下需求时使用此技能：
- "开发一个 xxx 管理页面"
- "新建一个前端模块"
- "写一个 CRUD 页面"
- "添加 xxx 列表页"
- 任何涉及 `web/src/views/` 下新增页面的需求

---

## 一、项目规范速查

### 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.5+ | 核心框架（Composition API） |
| TypeScript | 6.0+ | 类型安全 |
| Vite | 8.0+ | 构建工具 |
| Element Plus | 2.13+ | UI 组件库 |
| @pureadmin/table | 3.3+ | 表格组件（pure-table） |
| @pureadmin/utils | 2.6+ | 工具函数库 |
| Pinia | 3.0+ | 状态管理 |
| Tailwind CSS | 4.2+ | 原子化 CSS |

### 目录结构

```
web/src/views/<domain>/<module>/
├── index.vue          # 主页面（PureTableBar + pure-table）
├── form.vue           # 对话框表单组件
└── utils/
    ├── hook.tsx       # Composable（所有业务逻辑）
    ├── types.ts       # TypeScript 类型定义
    └── rule.ts        # 表单校验规则
```

### 命名规范

| 概念 | 规范 | 示例 |
|------|------|------|
| 页面组件名 | `System{{Name}}` | `SystemRole`、`SystemProduct` |
| defineOptions name | 与路由 name 一致 | `defineOptions({ name: "SystemRole" })` |
| Composable 函数 | `use{{Name}}` | `useRole()`、`useProduct()` |
| API 实例 | `{{name}}Api` | `roleApi`、`productApi` |
| 类型接口 | `FormItemProps`、`FormProps` | 每个模块的 types.ts 中定义 |

### 组件选择规范

| 场景 | 使用 | 不要使用 |
|------|------|----------|
| 对话框 | `addDialog` (ReDialog) | 内联 `el-dialog` |
| 抽屉 | `addDrawer` (ReDrawer) | 内联 `el-drawer` |
| 表格工具栏 | `PureTableBar` | 自定义工具栏 |
| 表格 | `pure-table` | 原生 `el-table` |
| 分页 | pure-table 内置分页 | 单独 `el-pagination` |
| 图标 | `useRenderIcon` | 直接引用图标组件 |
| 权限-路由级 | `ReAuth` / `v-auth` | 自行判断 |
| 权限-按钮级 | `RePerms` / `v-perms` | 自行判断 |

### 导入规范

```typescript
// API 导入 — 统一使用类实例，从模块化路径导入
import { roleApi } from "@/api/system/role";

// 类型导入 — 统一从 base.ts 导入
import { type Result, type ResultTable } from "@/api/base";

// 共享 Composables — 从统一入口导入
import { useCrudTable, useSwitchStatus, useDialogForm } from "@/composables";

// 公共 Hooks — 从 system hooks 导入
import { usePublicHooks, formatHigherDeptOptions, formatHigherMenuOptions } from "@/views/system/hooks";

// @pureadmin/utils — 按需导入
import { deviceDetection, getKeyList, isAllEmpty } from "@pureadmin/utils";
```

---

## 二、BaseApi 基类 API

所有前端 API 类继承自 `BaseApi`（定义在 `web/src/api/base.ts`）。

### 标准方法

| 方法 | 签名 | HTTP | 说明 |
|------|------|------|------|
| list | `list<T>(params?)` | POST `/{prefix}` | 分页列表 |
| retrieve | `retrieve<T>(id)` | GET `/{prefix}/{id}` | 获取详情 |
| create | `create<T>(data)` | POST `/{prefix}/create` | 创建 |
| partialUpdate | `partialUpdate<T>(id, data)` | PUT `/{prefix}/{id}` | 更新 |
| destroy | `destroy(id)` | DELETE `/{prefix}/{id}` | 删除 |
| batchDelete | `batchDelete(ids)` | POST `/{prefix}/batch-delete` | 批量删除 |
| updateStatus | `updateStatus(id, data)` | PUT `/{prefix}/{id}/status` | 修改状态 |

### 通用类型

```typescript
// 分页结果
type ResultTable<T> = { code: number; message: string; data?: { list: Array<T>; total?: number; pageSize?: number; currentPage?: number } };
// 通用结果
type Result<T> = { code: number; message: string; data?: T };
// 分页参数
type PageParams = { pageNum?: number; pageSize?: number; [key: string]: any };
```

### 子类示例

```typescript
class RoleApi extends BaseApi {
  constructor() { super("/role"); }
  // 覆写 list 返回 ResultTable
  list<T = any>(params?: object): Promise<ResultTable<T>> {
    return http.request<ResultTable<T>>("post", this.prefix, { data: params });
  }
  // 扩展领域方法
  getRoleMenu() { return http.request<Result>("get", `${this.prefix}/menu`); }
  getRoleMenuIds(data: object) { return http.request<Result>("post", `${this.prefix}/menu-ids`, { data }); }
  saveRoleMenu(id: string, menuIds: string[]) { return http.request<Result>("put", `${this.prefix}/${id}/menu`, { data: { menuIds } }); }
}
export const roleApi = new RoleApi();
```

---

## 三、共享 Composables API

### 3.1 useCrudTable

封装分页、搜索、删除等通用 CRUD 表格逻辑。

**配置项 `UseCrudTableOptions`：**

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| api | BaseApi | 是 | - | API 实例 |
| searchForm | Record\<string, any\> | 是 | - | 搜索表单 reactive |
| displayField | string | 是 | - | 删除确认显示字段 |
| entityName | string | 是 | - | 实体中文名 |
| listMode | 'paginated' \| 'tree' | 否 | 'paginated' | 列表模式 |
| immediate | boolean | 否 | true | 是否自动搜索 |

**返回值：**

| 属性 | 类型 | 说明 |
|------|------|------|
| loading | Ref\<boolean\> | 加载状态 |
| dataList | Ref\<any[]\> | 数据列表 |
| pagination | PaginationProps | 分页配置（已初始化 `{ total: 0, pageSize: 10, currentPage: 1, background: true }`） |
| onSearch | () => Promise\<void\> | 搜索（自动 loading + 数据填充 + 分页更新） |
| resetForm | (formEl?) => void | 重置表单并搜索 |
| handleDelete | (row) => Promise\<void\> | 删除（含 ElMessageBox.confirm 确认弹窗） |
| handleBatchDelete | (ids) => Promise\<void\> | 批量删除（含确认弹窗） |
| handleSizeChange | (val) => void | 每页条数变化（自动更新 pagination 并 onSearch） |
| handleCurrentChange | (val) => void | 当前页变化（自动更新 pagination 并 onSearch） |

**使用示例：**

```typescript
import { useCrudTable } from "@/composables";
import { roleApi } from "@/api/system/role";

const form = reactive({ name: "", code: "", isActive: "" });

const {
  loading, dataList, pagination,
  onSearch, resetForm, handleDelete,
  handleBatchDelete, handleSizeChange, handleCurrentChange
} = useCrudTable({
  api: roleApi,
  searchForm: form,
  displayField: "name",
  entityName: "角色"
});
```

### 3.2 useSwitchStatus

封装 el-switch 状态切换的确认弹窗、API 调用、加载状态管理。

**配置项 `UseSwitchStatusOptions`：**

| 属性 | 类型 | 必填 | 说明 |
|------|------|------|------|
| api | BaseApi | 是 | API 实例（需支持 updateStatus） |
| displayField | string | 是 | 确认弹窗显示的字段名 |
| entityName | string | 是 | 实体中文名 |

**返回值：**

| 属性 | 类型 | 说明 |
|------|------|------|
| switchLoadMap | Ref\<Record\> | 每行开关加载状态映射 |
| switchStyle | ComputedRef | 开关样式（绿色 `#6abe39` / 红色 `#e84749`） |
| onChange | (scope) => void | 状态变更处理（ElMessageBox.confirm → api.updateStatus → message） |
| createSwitchRenderer | () => CellRendererFn | 生成开关列的 cellRenderer |

**使用示例：**

```typescript
import { useSwitchStatus } from "@/composables";
import { roleApi } from "@/api/system/role";

const { createSwitchRenderer } = useSwitchStatus({
  api: roleApi,
  displayField: "name",
  entityName: "角色"
});

// 在 columns 中使用
const columns: TableColumnList = [
  // ...
  {
    label: "状态",
    prop: "isActive",
    minWidth: 90,
    cellRenderer: createSwitchRenderer()
  },
  // ...
];
```

`createSwitchRenderer()` 生成的 cellRenderer 渲染 `el-switch`，包含：
- `size` 自动适配（small/default）
- `switchLoadMap` 加载状态管理
- `active-value={1}` / `inactive-value={0}`
- `inline-prompt` + `active-text="已启用"` / `inactive-text="已停用"`
- 自动绑定 `onChange` 处理

### 3.3 useDialogForm

封装 addDialog + 表单验证 + 新增/更新提交逻辑。

**配置项 `UseDialogFormOptions`：**

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| formComponent | Component | 是 | - | 表单 Vue 组件 |
| entityName | string | 是 | - | 中文名 |
| fieldMappings | FieldMapping[] | 是 | - | 字段映射配置 |
| api | BaseApi | 是 | - | API 实例 |
| width | string | 否 | "40%" | 对话框宽度 |
| onSuccess | () => void | 否 | - | 成功后回调（通常为 onSearch） |

**FieldMapping 配置：**

| 属性 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| key | string | 是 | - | 字段名 |
| defaultValue | any | 否 | "" | 新增时的默认值 |
| nullable | boolean | 否 | false | 空值转 null |
| rowKey | string | 否 | 同 key | 从 row 取值的键名 |

**返回值：**

| 属性 | 类型 | 说明 |
|------|------|------|
| formRef | Ref | 表单组件 ref |
| openDialog | (title?, row?) => void | 打开对话框（title 默认 "新增"） |

**使用示例：**

```typescript
import { useDialogForm } from "@/composables";
import editForm from "../form.vue";
import { roleApi } from "@/api/system/role";

const { openDialog } = useDialogForm({
  formComponent: editForm,
  entityName: "角色",
  api: roleApi,
  fieldMappings: [
    { key: "name", defaultValue: "" },
    { key: "code", defaultValue: "" },
    { key: "description", defaultValue: "", nullable: true }
  ],
  width: "40%",
  onSuccess: onSearch
});
```

**openDialog 内部流程：**

1. 调用 `addDialog()` 配置：`draggable: true`、`fullscreen: deviceDetection()`、`fullscreenIcon: true`、`closeOnClickModal: false`
2. `contentRenderer` 通过 `h(formComponent, { ref: formRef })` 渲染表单
3. `beforeSure` 中：`formRef.value.getRef().validate()` → 构建 payload → 判断新增/更新 → API 调用 → `done()` + `onSuccess()`
4. `fieldMappings` 中 `nullable: true` 的字段，空值自动转为 `null`

---

## 四、ReDialog 完整 API（addDialog）

> 参考：`web/src/components/ReDialog/type.ts`

### 导入

```typescript
import { addDialog, closeDialog, updateDialog, closeAllDialog } from "@/components/ReDialog";
import type { DialogOptions, ButtonProps } from "@/components/ReDialog";
```

### 函数 API

| 函数 | 签名 | 说明 |
|------|------|------|
| addDialog | `(options: DialogOptions) => void` | 打开对话框 |
| closeDialog | `(options: DialogOptions, index: number, args?: any) => void` | 关闭指定对话框 |
| updateDialog | `(value: any, key?: string, index?: number) => void` | 更新对话框属性（默认 key 为 "title"） |
| closeAllDialog | `() => void` | 关闭所有对话框 |

### DialogOptions 接口

DialogOptions 继承 Element Plus `el-dialog` 所有属性，关键扩展字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| **props** | `any` | 传递给 contentRenderer 组件的 props（通过 v-bind 绑定） |
| **hideFooter** | `boolean` | 是否隐藏底部按钮区 |
| **popconfirm** | `Popconfirm` | 确定按钮的气泡确认框配置 |
| **sureBtnLoading** | `boolean` | 确定按钮是否显示 loading |
| **headerRenderer** | `({ close, titleId, titleClass }) => VNode` | 自定义标题渲染器 |
| **contentRenderer** | `({ options, index }) => VNode` | 自定义内容渲染器 |
| **footerRenderer** | `({ options, index }) => VNode` | 自定义底部渲染器（覆盖默认按钮） |
| **footerButtons** | `ButtonProps[]` | 自定义底部按钮列表 |
| **open** | `({ options, index }) => void` | 打开后回调 |
| **close** | `({ options, index }) => void` | 关闭后回调（仅关闭按钮/ESC/空白触发） |
| **closeCallBack** | `({ options, index, args }) => void` | 关闭后回调（args.command: "cancel"/"sure"/"close"） |
| **fullscreenCallBack** | `({ options, index }) => void` | 全屏切换回调 |
| **beforeCancel** | `(done, { options, index }) => void` | 取消前拦截（需调用 done() 关闭） |
| **beforeSure** | `(done, { options, index, closeLoading }) => void` | 确认前拦截（需调用 done() 关闭） |

### beforeSure/beforeCancel — done 模式

对话框**不会**自动关闭，必须调用 `done()` 才会关闭：

```typescript
beforeSure: (done, { options, index, closeLoading }) => {
  // closeLoading() — 仅关闭确定按钮的 loading，不关闭对话框
  // done() — 关闭 loading 并关闭对话框

  formRef.value.getRef().validate(valid => {
    if (valid) {
      // API 调用...
      done();      // 关闭对话框
      onSearch();  // 刷新表格
    }
  });
}
```

### contentRenderer 四种写法

```typescript
// 1. h() 函数（推荐，本项目标准写法）
contentRenderer: () => h(editForm, { ref: formRef, formInline: null })

// 2. JSX 内联组件
contentRenderer: () => <editForm ref={formRef} formInline={null} />

// 3. JSX 内联内容
contentRenderer: () => <p>简单内容</p>

// 4. createVNode
contentRenderer: () => createVNode(forms, { formInline: value })
```

> **注意**：当使用 `h(formComponent, { ref: formRef, formInline: null })` 时，`formInline: null` 表示让组件使用 `props` 中的 `formInline` 值（通过 `v-bind="options.props"` 自动传递）。

### 默认底部按钮

当未提供 `footerRenderer` 和 `footerButtons` 时，默认渲染：
- **取消**：`text: true, bg: true`，调用 `beforeCancel` 或直接关闭
- **确定**：`type: "primary", text: true, bg: true`，调用 `beforeSure` 或直接关闭

### CRUD 标准 addDialog 配置

```typescript
addDialog({
  title: `${title}${entityName}`,
  props: { formInline: { name: row?.name ?? "", code: row?.code ?? "" } },
  width: "40%",
  draggable: true,
  fullscreen: deviceDetection(),  // 移动端自动全屏
  fullscreenIcon: true,
  closeOnClickModal: false,
  contentRenderer: () => h(editForm, { ref: formRef, formInline: null }),
  beforeSure: (done, { options }) => {
    const FormRef = formRef.value.getRef();
    const curData = options.props.formInline as FormItemProps;

    // chores 模式 — vue-pure-admin 官方推荐结构
    function chores() {
      message(`成功${title}${entityName} ${curData.name}`, { type: "success" });
      done();
      onSearch();
    }

    FormRef.validate(valid => {
      if (valid) {
        if (title === "新增") {
          api.create(payload).then(() => chores());
        } else {
          api.partialUpdate(row.id, payload).then(() => chores());
        }
      }
    });
  }
});
```

---

## 五、ReDrawer 完整 API（addDrawer）

> 参考：`web/src/components/ReDrawer/type.ts`

### 导入

```typescript
import { addDrawer, closeDrawer, updateDrawer, closeAllDrawer } from "@/components/ReDrawer";
import type { DrawerOptions } from "@/components/ReDrawer";
```

### DrawerOptions 接口

与 DialogOptions 结构完全对称，差异仅在 Drawer 特有属性：

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| direction | `"rtl" \| "ltr" \| "ttb" \| "btt"` | `"rtl"` | 打开方向 |
| size | `string \| number` | `"30%"` | 抽屉尺寸 |
| resizable | `boolean` | `false` | 可调整大小 |
| withHeader | `boolean` | `true` | 是否显示 header |

> **注意**：ReDrawer 中气泡确认字段名为 `popConfirm`（大写 C），而 ReDialog 中为 `popconfirm`（小写 c）。

### 标准用法

```typescript
addDrawer({
  title: "标题",
  direction: "rtl",
  size: "40%",
  props: { formInline: { ... } },
  closeOnClickModal: false,
  contentRenderer: () => h(FormComponent, { ref: formRef }),
  beforeSure: (done) => {
    // 验证 + 提交
    done();
  }
});
```

---

## 六、RePureTableBar 完整 API

> 参考：`web/src/components/RePureTableBar/`

### 导入

```typescript
import { PureTableBar } from "@/components/RePureTableBar";
```

### Props

| Prop | 类型 | 默认 | 说明 |
|------|------|------|------|
| title | String | "列表" | 标题文本 |
| columns | Array\<TableColumnList\> | [] | 列定义（用于列设置：显隐/排序/固定） |
| tableRef | Object | - | 表格实例 ref（提供时显示展开/折叠功能） |
| isExpandAll | Boolean | true | 树形表格默认展开状态 |
| tableKey | String \| Number | "0" | 列设置 checkbox group 的唯一 key |

### Emits

| 事件 | 参数 | 说明 |
|------|------|------|
| refresh | - | 刷新按钮点击 |
| fullscreen | boolean | 全屏切换 |

### Slots

| 插槽 | 作用域 | 说明 |
|------|--------|------|
| title | - | 自定义标题区域 |
| buttons | - | 操作按钮区域（在工具栏图标之前） |
| default | `{ size, dynamicColumns }` | **主内容区域** |

### default 作用域详解

```typescript
{
  size: "large" | "default" | "small",  // 当前表格密度
  dynamicColumns: TableColumnList       // 经过显隐/排序/固定处理后的列
}
```

- `size` 在用户点击密度下拉菜单时自动变化
- `dynamicColumns` 反映用户在列设置中的显隐、拖拽排序、左右固定操作

### 工具栏内置功能

从右到左依次为：全屏切换 → 列设置 → 密度选择 → 刷新 → 展开/折叠（仅 treeRef 模式）

### 标准用法

```vue
<PureTableBar
  title="{{chinese_name}}管理"
  :columns="columns"
  @refresh="onSearch"
>
  <template #buttons>
    <el-button type="primary" :icon="useRenderIcon(AddFill)" @click="openDialog()">
      新增{{chinese_name}}
    </el-button>
  </template>
  <template v-slot="{ size, dynamicColumns }">
    <pure-table
      :size="size"
      :columns="dynamicColumns"
      :data="dataList"
      :pagination="{ ...pagination, size }"
      :loading="loading"
    />
  </template>
</PureTableBar>
```

---

## 七、CRUD 页面模板

### 7.1 类型定义 (`utils/types.ts`)

```typescript
interface FormItemProps {
  {{fields_form_item_props}}
  isActive: number;
  description: string;
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
```

### 7.2 校验规则 (`utils/rule.ts`)

```typescript
import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
{{required_field_rules}}
});
```

必填字段规则格式：`fieldName: [{ required: true, message: "{{字段中文名}}为必填项", trigger: "blur" }]`

### 7.3 核心 Hook (`utils/hook.tsx`)

```typescript
import dayjs from "dayjs";
import editForm from "../form.vue";
import { {{name}}Api } from "@/api/system/{{name}}";
import { useCrudTable, useSwitchStatus, useDialogForm } from "@/composables";
import type { FormItemProps } from "../utils/types";

export function use{{Name}}() {
  const form = reactive({
    {{search_form_fields}}
  });

  const {
    loading, dataList, pagination,
    onSearch, resetForm, handleDelete,
    handleSizeChange, handleCurrentChange
  } = useCrudTable({
    api: {{name}}Api,
    searchForm: form,
    displayField: "{{display_field}}",
    entityName: "{{chinese_name}}"
  });

  const { createSwitchRenderer } = useSwitchStatus({
    api: {{name}}Api,
    displayField: "{{display_field}}",
    entityName: "{{chinese_name}}"
  });

  const { openDialog } = useDialogForm({
    formComponent: editForm,
    entityName: "{{chinese_name}}",
    api: {{name}}Api,
    fieldMappings: [
      {{field_mappings_config}}
    ],
    width: "40%",
    onSuccess: onSearch
  });

  const columns: TableColumnList = [
    {{table_columns}}
    {
      label: "状态",
      prop: "isActive",
      minWidth: 90,
      cellRenderer: createSwitchRenderer()
    },
    {
      label: "创建时间",
      minWidth: 160,
      prop: "createdTime",
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "操作",
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];

  return {
    form, loading, columns, dataList, pagination,
    onSearch, resetForm, openDialog, handleDelete,
    handleSizeChange, handleCurrentChange
  };
}
```

**对比旧写法的改进：**

| 旧写法（每个 hook.tsx 重复） | 新写法（使用 composables） |
|------|------|
| 手动定义 `pagination = reactive({...})` | `useCrudTable` 内置初始化 |
| 手写 `onSearch()` 含 loading/data/pagination | `useCrudTable` 统一处理 |
| 手写 `resetForm()` | `useCrudTable` 统一处理 |
| 手写 `handleDelete()` 含 ElMessageBox | `useCrudTable` 统一处理 |
| `handleSizeChange` 只 console.log | `useCrudTable` 自动更新分页并搜索 |
| 手写 `onChange()` 含 switchLoadMap + confirm + API | `useSwitchStatus` + `createSwitchRenderer()` |
| 手写 `openDialog()` 含 addDialog + validate + create/update | `useDialogForm` 统一处理 |

### 7.4 表单组件 (`form.vue`)

```vue
<script setup lang="ts">
import { ref } from "vue";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    {{form_default_values}}
    isActive: 1,
    description: ""
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);

/** 暴露 el-form 实例给父组件，用于 beforeSure 中调用 validate */
function getRef() {
  return ruleFormRef.value;
}

defineExpose({ getRef });
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="newFormInline"
    :rules="formRules"
    label-width="82px"
  >
    {{form_items_template}}
    <el-form-item label="状态">
      <el-switch
        v-model="newFormInline.isActive"
        :active-value="1"
        :inactive-value="0"
        inline-prompt
        active-text="启用"
        inactive-text="停用"
      />
    </el-form-item>

    <el-form-item label="描述">
      <el-input
        v-model="newFormInline.description"
        placeholder="请输入描述信息"
        type="textarea"
      />
    </el-form-item>
  </el-form>
</template>
```

**关键模式**：表单组件通过 `defineExpose({ getRef })` 暴露底层 `el-form` 实例，使 hook.tsx 的 `beforeSure` 中能调用 `formRef.value.getRef().validate()`。

**字段到表单组件映射：**

| 字段类型 | 组件 | 代码 |
|----------|------|------|
| str（短文本） | el-input | `<el-input v-model="newFormInline.fieldName" clearable placeholder="请输入{{字段中文名}}" />` |
| str（长文本） | el-input textarea | `<el-input v-model="newFormInline.fieldName" placeholder="请输入{{字段中文名}}" type="textarea" />` |
| int | el-input-number | `<el-input-number v-model="newFormInline.fieldName" class="w-full!" :min="0" controls-position="right" />` |
| float | el-input-number | `<el-input-number v-model="newFormInline.fieldName" class="w-full!" :min="0" :precision="2" controls-position="right" />` |
| is_active | el-switch | 已内置在模板中 |
| parentId | el-cascader | 树形模式下使用 |
| description | el-input textarea | 已内置在模板中 |

### 7.5 主页面 (`index.vue`)

```vue
<script setup lang="ts">
import { ref } from "vue";
import { use{{Name}} } from "./utils/hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "System{{Name}}"
});

const formRef = ref();
const tableRef = ref();

const {
  form, loading, columns, dataList, pagination,
  onSearch, resetForm, openDialog, handleDelete,
  handleSizeChange, handleCurrentChange
} = use{{Name}}();
</script>

<template>
  <div class="main">
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
    >
      {{search_form_items}}
      <el-form-item>
        <el-button
          type="primary"
          :icon="useRenderIcon('ri/search-line')"
          :loading="loading"
          @click="onSearch"
        >搜索</el-button>
        <el-button :icon="useRenderIcon(Refresh)" @click="resetForm(formRef)">重置</el-button>
      </el-form-item>
    </el-form>

    <PureTableBar
      title="{{chinese_name}}管理"
      :columns="columns"
      @refresh="onSearch"
    >
      <template #buttons>
        <el-button
          type="primary"
          :icon="useRenderIcon(AddFill)"
          @click="openDialog()"
        >新增{{chinese_name}}</el-button>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <pure-table
          ref="tableRef"
          align-whole="center"
          showOverflowTooltip
          table-layout="auto"
          :loading="loading"
          :size="size"
          adaptive
          :adaptiveConfig="{ offsetBottom: 108 }"
          :data="dataList"
          :columns="dynamicColumns"
          :pagination="{ ...pagination, size }"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        >
          <template #operation="{ row }">
            <el-button
              class="reset-margin"
              link
              type="primary"
              :size="size"
              :icon="useRenderIcon(EditPen)"
              @click="openDialog('修改', row)"
            >修改</el-button>
            <el-popconfirm
              :title="`是否确认删除{{chinese_name}}名称为${row.{{display_field}}}的这条数据`"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
                  class="reset-margin"
                  link
                  type="primary"
                  :size="size"
                  :icon="useRenderIcon(Delete)"
                >删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </pure-table>
      </template>
    </PureTableBar>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}

.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
</style>
```

---

## 八、ReAuth / RePerms（权限控制）

### 路由级权限（meta.auths）

权限标识定义在路由的 `meta.auths` 中，同一路由内唯一，跨路由可复用。

```vue
<!-- 组件方式 -->
<Auth value="btn_add"><el-button>新增</el-button></Auth>

<!-- 指令方式（不可动态修改） -->
<el-button v-auth="'btn_add'">新增</el-button>

<!-- 函数方式 -->
<el-button v-if="hasAuth('btn_add')">新增</el-button>
```

### 按钮级权限（API 返回 permissions）

权限标识来自登录 API 响应，必须全局唯一。

```vue
<Perms value="user:btn:add"><el-button>新增</el-button></Perms>
<el-button v-perms="'user:btn:add'">新增</el-button>
<el-button v-if="hasPerms('user:btn:add')">新增</el-button>
```

---

## 九、@pureadmin/utils 使用指南

### 常用函数速查

| 函数 | 用途 | 使用场景 |
|------|------|----------|
| `deviceDetection()` | 移动端检测 | addDialog 的 fullscreen 参数 |
| `getKeyList(arr, key)` | 提取数组中指定 key 的值列表 | 批量删除时提取 ids |
| `isAllEmpty(val)` | 判断值是否为空 | 表单空值判断 |
| `hideTextAtIndex(str, opts)` | 隐藏字符串中间部分 | 手机号脱敏 `{ start: 3, end: 6 }` |
| `useDark()` | 暗色模式切换 | 主题适配（isDark ref） |
| `storageLocal()` | localStorage 类型安全封装 | 本地持久化 |
| `storageSession()` | sessionStorage 类型安全封装 | 会话级持久化 |
| `debounce(fn, timeout)` | 防抖 | 搜索输入 |
| `throttle(fn, timeout)` | 节流 | 滚动/窗口调整 |
| `clone(obj, deep?)` | 克隆对象 | 数据复制 |
| `cloneDeep(obj)` | 深拷贝 | 复杂对象复制 |
| `delay(ms)` | 延迟（返回 Promise） | 异步等待 |
| `downloadByData(data, filename)` | 下载文件 | 导出功能 |
| `downloadByUrl(url, filename)` | 通过 URL 下载 | 远程文件下载 |
| `getCurrentDate(opts?)` | 获取当前日期 | 日期显示 |
| `isUrl(str)` / `isEmail(str)` / `isPhone(str)` | 格式校验 | 表单校验 |

### 使用示例

```typescript
import { deviceDetection, getKeyList, isAllEmpty, hideTextAtIndex } from "@pureadmin/utils";

// 移动端检测 — addDialog 中使用
fullscreen: deviceDetection()

// 提取 id 列表 — 批量操作
const ids = getKeyList(selectedRows, "id");

// 手机号脱敏
formatter: ({ phone }) => phone ? hideTextAtIndex(phone, { start: 3, end: 6 }) : "-"

// 空值判断
if (isAllEmpty(searchValue)) { ... }
```

---

## 十、样式规范

### 搜索表单

```html
<el-form
  :inline="true"
  :model="form"
  class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
>
```

搜索项使用 `class="w-45!"` 限制宽度，或使用 `clearable` 属性。

### 表格

```html
<pure-table
  align-whole="center"
  showOverflowTooltip
  table-layout="auto"
  adaptive
  :adaptiveConfig="{ offsetBottom: 108 }"
  :header-cell-style="{
    background: 'var(--el-fill-color-light)',
    color: 'var(--el-text-color-primary)'
  }"
>
```

### 固定样式片段

每个页面的 `<style>` 中包含：

```scss
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}
.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
```

### Tailwind 常用类

| 场景 | 类名 |
|------|------|
| 按钮重置边距 | `reset-margin` |
| 全宽 | `w-full!` |
| 搜索框宽度 | `w-45!` |
| 居中 | `flex-c` |
| 圆形头像 | `size-6 rounded-full align-middle` |

---

## 十一、反模式清单

### 禁止

1. **禁止使用内联 el-dialog** — 统一使用 `addDialog`（ReDialog）
2. **禁止从 `@/api/system` 导入函数** — 使用类实例导入 `@/api/system/xxx`
3. **禁止在 hook.tsx 中重复定义 pagination** — 使用 `useCrudTable`
4. **禁止 handleSizeChange/handleCurrentChange 只 console.log** — 使用 `useCrudTable` 自动处理
5. **禁止手写 switch onChange 重复逻辑** — 使用 `useSwitchStatus`
6. **禁止使用 setTimeout 模拟 loading 延迟** — 直接设置 `loading.value = false`
7. **禁止在多处定义 Result/ResultTable 类型** — 统一从 `@/api/base` 导入
8. **禁止在 beforeSure 中不调用 done()** — 对话框不会自动关闭，必须调用 `done()`
9. **禁止在 contentRenderer 中不传递 ref** — 表单组件需要 `ref: formRef` 才能 validate

### 推荐

1. 使用共享 composables 减少代码量
2. 使用 `createSwitchRenderer()` 生成开关列
3. 使用 `useRenderIcon` 渲染图标
4. 搜索表单使用 `toRaw(form)` 传给 API
5. 表单空字符串字段使用 `nullable: true` 配置自动转 null
6. 列定义中状态列使用 `createSwitchRenderer()`
7. 时间列使用 dayjs 格式化
8. 使用 `chores()` 模式组织 beforeSure 中的成功逻辑

---

## 十二、树形模式特殊处理

当模块包含 `parent_id` 字段时为树形模式，需注意以下差异：

### useCrudTable 配置

```typescript
useCrudTable({
  listMode: "tree",  // 改为 tree
  // 无分页参数
});
```

树形模式下 `onSearch` 使用 `handleTree(data)` 转换数据，无分页。

### 列定义差异

- 不需要分页列
- 可能需要展示层级关系列
- 使用 `PureTableBar` 的 `tableRef` + `isExpandAll` 控制展开折叠

### 表单差异

- `parentId` 字段使用 `el-cascader` 选择父级
- 需要加载树形选项数据

---

## 十三、验证清单

代码生成后，按以下顺序验证：

### 1. 编译检查

```bash
cd web
pnpm build
```

### 2. TypeScript 检查

```bash
pnpm typecheck
```

### 3. 代码规范检查

```bash
pnpm lint
```

### 4. 功能验证

- 页面路由正确加载（需后端菜单配置）
- 列表数据正常展示
- 搜索/重置功能正常
- 分页切换正常（handleSizeChange/handleCurrentChange 应自动搜索）
- 新增对话框正常弹出、提交成功
- 编辑对话框正常弹出、数据回填正确
- 删除确认弹窗正常、删除成功
- 状态开关切换正常
- 表格工具栏（刷新/密度/列设置/全屏）正常

### 5. 移动端验证

- 对话框自动全屏（deviceDetection）
- 表格自适应宽度

### 注意事项

- 前端路由由后端菜单 API 动态驱动，新页面需管理员在菜单管理中配置
- 确保 `defineOptions({ name })` 与路由 `name` 一致
- API 实例必须继承 `BaseApi`（定义在 `@/api/base.ts`）
- 所有中文注释和提示文本
- 确保前后端服务同时运行才能联调
- `form.vue` 中必须 `defineExpose({ getRef })` 暴露 el-form 实例
- `addDialog` 的 `beforeSure` 中必须调用 `done()` 才会关闭对话框
