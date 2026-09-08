import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { transformI18n } from "@/plugins/i18n";
import { useCrudTable, useSwitchStatus, useDialogForm } from "@/composables";
import { getKeyList } from "@pureadmin/utils";
import { roleApi } from "@/api/system/role";
import { deptApi } from "@/api/system/dept";
import { type Ref, reactive, ref, onMounted, watch, nextTick } from "vue";

/** 数据权限范围枚举（与后端 DataScope 一致）：1全部/2自定义/3本部门/4本部门及以下/5仅本人 */
const DataScope = {
  ALL: 1,
  CUSTOM: 2,
  DEPT: 3,
  DEPT_AND_CHILD: 4,
  SELF: 5
} as const;

export function useRole(treeRef: Ref) {
  const form = reactive({
    name: "",
    code: "",
    isActive: ""
  });

  const curRow = ref();
  const treeIds = ref([]);
  const treeData = ref([]);
  const isShow = ref(false);
  const isLinkage = ref(false);
  const treeSearchValue = ref();
  const isExpandAll = ref(false);
  const isSelectAll = ref(false);
  const treeProps = {
    value: "id",
    label: "title",
    children: "children"
  };

  const {
    loading,
    dataList,
    pagination,
    onSearch,
    resetForm,
    handleDelete,
    handleSizeChange,
    handleCurrentChange
  } = useCrudTable({
    api: roleApi,
    searchForm: form,
    displayField: "name",
    entityName: "角色",
    immediate: false
  });

  const { createSwitchRenderer } = useSwitchStatus({
    api: roleApi,
    displayField: "name",
    entityName: "角色"
  });

  const { openDialog } = useDialogForm({
    formComponent: editForm,
    entityName: "角色",
    api: roleApi,
    fieldMappings: [
      { key: "name", defaultValue: "" },
      { key: "code", defaultValue: "" },
      { key: "isActive", defaultValue: 1 },
      { key: "dataScope", defaultValue: DataScope.ALL },
      { key: "description", defaultValue: "", nullable: true }
    ],
    width: "40%",
    onSuccess: onSearch
  });

  const columns: TableColumnList = [
    {
      label: "角色编号",
      prop: "id"
    },
    {
      label: "角色名称",
      prop: "name"
    },
    {
      label: "角色标识",
      prop: "code"
    },
    {
      label: "状态",
      minWidth: 90,
      cellRenderer: createSwitchRenderer()
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 160
    },
    {
      label: "创建时间",
      prop: "createdTime",
      minWidth: 160,
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "更新时间",
      prop: "updatedTime",
      minWidth: 160,
      formatter: ({ updatedTime }) =>
        updatedTime ? dayjs(updatedTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "操作",
      fixed: "right",
      width: 280,
      slot: "operation"
    }
  ];

  /** 菜单权限 */
  async function handleMenu(row?: any) {
    const { id } = row;
    if (id) {
      curRow.value = row;
      isShow.value = true;
      const { code, data } = await roleApi.getRoleMenuIds({ id });
      if (code === 0) {
        treeRef.value.setCheckedKeys(data);
      }
    } else {
      curRow.value = null;
      isShow.value = false;
    }
  }

  /** 高亮当前权限选中行 */
  function rowStyle({ row: { id } }) {
    return {
      cursor: "pointer",
      background: id === curRow.value?.id ? "var(--el-fill-color-light)" : ""
    };
  }

  /** 菜单权限-保存 */
  async function handleSave() {
    const { id, name } = curRow.value;
    const menuIds = treeRef.value.getCheckedKeys();

    try {
      const { code } = await roleApi.saveRoleMenu(id, menuIds);
      if (code === 0) {
        message(`角色 ${name} 的菜单权限修改成功`, { type: "success" });
      }
    } catch {
      message("保存菜单权限失败", { type: "error" });
    }
  }

  const onQueryChanged = (query: string) => {
    treeRef.value!.filter(query);
  };

  /** 数据权限-抽屉显隐 */
  const dataScopeVisible = ref(false);
  /** 数据权限-当前角色行 */
  const dataScopeRow = ref<any>({});
  /** 数据权限-表单 */
  const dataScopeForm = reactive<{ dataScope: number; deptIds: string[] }>({
    dataScope: DataScope.ALL,
    deptIds: []
  });
  /** 数据权限-部门树引用 */
  const deptTreeRef = ref();
  /** 数据权限-部门树数据 */
  const deptTreeData = ref([]);
  /** 数据权限-单选范围选项 */
  const dataScopeOptions = [
    { value: DataScope.ALL, label: "全部数据权限" },
    { value: DataScope.CUSTOM, label: "自定义数据权限" },
    { value: DataScope.DEPT, label: "本部门数据权限" },
    { value: DataScope.DEPT_AND_CHILD, label: "本部门及以下数据权限" },
    { value: DataScope.SELF, label: "仅本人数据权限" }
  ];
  /** 数据权限-部门树配置（部门树字段为 id/parentId/name/children） */
  const deptTreeProps = {
    value: "id",
    label: "name",
    children: "children"
  };

  /** 数据权限-打开抽屉并回填 */
  async function handleDataScope(row?: any) {
    dataScopeRow.value = row ?? {};
    dataScopeVisible.value = true;
    dataScopeForm.dataScope = DataScope.ALL;
    dataScopeForm.deptIds = [];

    // 部门树首次加载后缓存复用
    if (deptTreeData.value.length === 0) {
      const { code, data } = await deptApi.tree();
      if (code === 0) deptTreeData.value = data;
    }

    // 列表接口不返回 deptIds，需调用详情接口回填
    const { id } = dataScopeRow.value;
    const detailRes = await roleApi.retrieve(id);
    if (detailRes.code === 0 && detailRes.data) {
      dataScopeForm.dataScope = detailRes.data.dataScope ?? DataScope.ALL;
      dataScopeForm.deptIds = detailRes.data.deptIds ?? [];
    }
    await nextTick();
    if (dataScopeForm.dataScope === DataScope.CUSTOM) {
      deptTreeRef.value?.setCheckedKeys(dataScopeForm.deptIds);
    }
  }

  /** 数据权限-保存 */
  async function handleDataScopeSave() {
    const { id, name } = dataScopeRow.value;
    const deptIds =
      dataScopeForm.dataScope === DataScope.CUSTOM
        ? deptTreeRef.value.getCheckedKeys()
        : [];

    try {
      const { code } = await roleApi.changeDataScope(
        id,
        dataScopeForm.dataScope,
        deptIds
      );
      if (code === 0) {
        message(`角色 ${name} 的数据权限修改成功`, { type: "success" });
        dataScopeVisible.value = false;
        onSearch();
      }
    } catch {
      message("保存数据权限失败", { type: "error" });
    }
  }

  /** 数据权限-关闭时重置 */
  function handleDataScopeClose() {
    dataScopeVisible.value = false;
    dataScopeForm.dataScope = DataScope.ALL;
    dataScopeForm.deptIds = [];
    deptTreeRef.value?.setCheckedKeys([]);
  }

  // 非自定义范围时清空部门勾选
  watch(
    () => dataScopeForm.dataScope,
    val => {
      if (val !== DataScope.CUSTOM) {
        deptTreeRef.value?.setCheckedKeys([]);
      }
    }
  );

  const filterMethod = (query: string, node) => {
    return transformI18n(node.title)!.includes(query);
  };

  onMounted(async () => {
    onSearch();
    const { code, data } = await roleApi.getRoleMenu();
    if (code === 0) {
      treeIds.value = getKeyList(data, "id");
      treeData.value = handleTree(data);
    }
  });

  watch(isExpandAll, val => {
    val
      ? treeRef.value.setExpandedKeys(treeIds.value)
      : treeRef.value.setExpandedKeys([]);
  });

  watch(isSelectAll, val => {
    val
      ? treeRef.value.setCheckedKeys(treeIds.value)
      : treeRef.value.setCheckedKeys([]);
  });

  return {
    form,
    isShow,
    curRow,
    loading,
    columns,
    rowStyle,
    dataList,
    treeData,
    treeProps,
    isLinkage,
    pagination,
    isExpandAll,
    isSelectAll,
    treeSearchValue,
    DataScope,
    dataScopeOptions,
    dataScopeVisible,
    dataScopeRow,
    dataScopeForm,
    deptTreeData,
    deptTreeProps,
    deptTreeRef,
    onSearch,
    resetForm,
    openDialog,
    handleMenu,
    handleSave,
    handleDelete,
    handleDataScope,
    handleDataScopeSave,
    handleDataScopeClose,
    filterMethod,
    transformI18n,
    onQueryChanged,
    handleSizeChange,
    handleCurrentChange
  };
}
