import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { transformI18n } from "@/plugins/i18n";
import { useCrudTable, useSwitchStatus, useDialogForm } from "@/composables";
import { getKeyList } from "@pureadmin/utils";
import { roleApi } from "@/api/system/role";
import { type Ref, reactive, ref, onMounted, watch } from "vue";

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
      width: 210,
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
    onSearch,
    resetForm,
    openDialog,
    handleMenu,
    handleSave,
    handleDelete,
    filterMethod,
    transformI18n,
    onQueryChanged,
    handleSizeChange,
    handleCurrentChange
  };
}
