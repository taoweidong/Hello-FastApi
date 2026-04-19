import { ref, onMounted, reactive, nextTick } from "vue";
import { message } from "@/utils/message";
import {
  getRoleList,
  getRoleMenu,
  getRoleMenuIds,
  saveRoleMenu
} from "@/api/system";
import type { FormInstance } from "element-plus";

export function usePermission() {
  const loading = ref(false);
  const menuLoading = ref(false);
  const saveLoading = ref(false);
  const roleList = ref([]);
  const menuTree = ref([]);
  const checkedMenuIds = ref([]);
  const currentRoleId = ref("");
  const treeRef = ref();
  const formRef = ref<FormInstance>();

  const pagination = reactive({
    total: 0,
    pageSize: 100,
    currentPage: 1,
    background: true
  });

  const roleColumns: TableColumnList = [
    {
      label: "角色名称",
      prop: "name",
      minWidth: 120
    },
    {
      label: "角色编码",
      prop: "code",
      minWidth: 100
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 160,
      showOverflowTooltip: true
    },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 80,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={row.isActive === 1 ? "success" : "danger"}
        >
          {row.isActive === 1 ? "启用" : "停用"}
        </el-tag>
      )
    },
    {
      label: "操作",
      fixed: "right",
      width: 100,
      slot: "operation"
    }
  ];

  async function fetchRoleList() {
    loading.value = true;
    try {
      const { code, data } = await getRoleList({
        pageNum: pagination.currentPage,
        pageSize: pagination.pageSize
      });
      if (code === 0) {
        roleList.value = data.list || [];
        pagination.total = data.total;
      }
    } catch {
      roleList.value = [];
    }
    loading.value = false;
  }

  async function fetchMenuTree() {
    menuLoading.value = true;
    try {
      const { code, data } = await getRoleMenu();
      if (code === 0) {
        menuTree.value = buildTree(data || []);
      }
    } catch {
      menuTree.value = [];
    }
    menuLoading.value = false;
  }

  async function selectRole(role: any) {
    currentRoleId.value = role.id;
    await fetchMenuTree();
    menuLoading.value = true;
    try {
      const { code, data } = await getRoleMenuIds({ id: role.id });
      if (code === 0) {
        checkedMenuIds.value = (data || []).map(String);
        await nextTick();
        treeRef.value?.setCheckedKeys(checkedMenuIds.value);
      }
    } catch {
      checkedMenuIds.value = [];
    }
    menuLoading.value = false;
  }

  async function handleSave() {
    if (!currentRoleId.value) {
      message("请先选择一个角色", { type: "warning" });
      return;
    }
    saveLoading.value = true;
    try {
      const checkedKeys = treeRef.value?.getCheckedKeys() || [];
      const halfCheckedKeys = treeRef.value?.getHalfCheckedKeys() || [];
      const menuIds = [...checkedKeys, ...halfCheckedKeys].map(String);
      const { code } = await saveRoleMenu(currentRoleId.value, menuIds);
      if (code === 0) {
        message("权限保存成功", { type: "success" });
      }
    } catch {
      message("保存失败", { type: "error" });
    }
    saveLoading.value = false;
  }

  function buildTree(data: any[], parentId = 0) {
    return data
      .filter(item => item.parentId === parentId)
      .map(item => ({
        id: String(item.id),
        label: item.title || item.name || "",
        parentId: item.parentId,
        menuType: item.menuType,
        children: buildTree(data, item.id)
      }))
      .sort((a, b) => (a.menuType || 0) - (b.menuType || 0));
  }

  onMounted(() => {
    fetchRoleList();
  });

  return {
    loading,
    menuLoading,
    saveLoading,
    roleList,
    menuTree,
    checkedMenuIds,
    currentRoleId,
    treeRef,
    formRef,
    pagination,
    roleColumns,
    fetchRoleList,
    selectRole,
    handleSave
  };
}
