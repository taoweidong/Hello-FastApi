import { ref, onMounted, reactive } from "vue";
import { message } from "@/utils/message";
import {
  getIpRuleList,
  createIpRule,
  updateIpRule,
  deleteIpRule,
  batchDeleteIpRule,
  clearIpRule
} from "@/api/system";
import { usePublicHooks } from "../hooks";
import type { FormInstance } from "element-plus";

export function useIpRule() {
  const loading = ref(true);
  const dataList = ref([]);
  const formRef = ref<FormInstance>();
  const selectedRows = ref([]);
  const { switchStyle } = usePublicHooks();

  const form = reactive({
    ruleType: "",
    isActive: ""
  });

  const pagination = reactive({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });

  const columns: TableColumnList = [
    {
      label: "勾选列",
      type: "selection",
      fixed: "left",
      reserveSelection: true
    },
    {
      label: "IP地址",
      prop: "ipAddress",
      minWidth: 150
    },
    {
      label: "规则类型",
      prop: "ruleType",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={row.ruleType === "whitelist" ? "success" : "danger"}>
          {row.ruleType === "whitelist" ? "白名单" : "黑名单"}
        </el-tag>
      )
    },
    {
      label: "原因",
      prop: "reason",
      minWidth: 200
    },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-switch
          v-model={row.isActive}
          active-value={1}
          inactive-value={0}
          inline-prompt
          active-text="启用"
          inactive-text="停用"
          style={switchStyle.value}
          onChange={() => handleUpdateStatus(row)}
        />
      )
    },
    {
      label: "过期时间",
      prop: "expiresAt",
      minWidth: 180,
      formatter: ({ expiresAt }) => expiresAt || "永不过期"
    },
    {
      label: "创建时间",
      prop: "createdAt",
      minWidth: 180
    },
    {
      label: "操作",
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];

  async function onSearch() {
    loading.value = true;
    try {
      const params: Record<string, any> = {
        pageNum: pagination.currentPage,
        pageSize: pagination.pageSize,
        ruleType: form.ruleType || undefined,
        isActive: form.isActive !== "" ? form.isActive : undefined
      };
      const { code, data } = await getIpRuleList(params);
      if (code === 0) {
        dataList.value = data.list || [];
        pagination.total = data.total;
        pagination.pageSize = data.pageSize;
        pagination.currentPage = data.currentPage;
      }
    } catch {
      dataList.value = [];
    }
    loading.value = false;
  }

  function resetForm(formEl: FormInstance | undefined) {
    form.ruleType = "";
    form.isActive = "";
    formEl?.resetFields();
    pagination.currentPage = 1;
    onSearch();
  }

  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    onSearch();
  }

  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  const dialogVisible = ref(false);
  const dialogTitle = ref("");
  const ruleForm = reactive({
    id: "",
    ipAddress: "",
    ruleType: "blacklist",
    reason: "",
    isActive: true,
    expiresAt: ""
  });

  function openDialog(title = "新增", row?: any) {
    dialogTitle.value = title;
    if (row) {
      Object.assign(ruleForm, {
        id: row.id,
        ipAddress: row.ipAddress,
        ruleType: row.ruleType,
        reason: row.reason,
        isActive: row.isActive === 1,
        expiresAt: row.expiresAt || ""
      });
    } else {
      Object.assign(ruleForm, {
        id: "",
        ipAddress: "",
        ruleType: "blacklist",
        reason: "",
        isActive: true,
        expiresAt: ""
      });
    }
    dialogVisible.value = true;
  }

  async function handleSubmit() {
    const data = {
      ipAddress: ruleForm.ipAddress,
      ruleType: ruleForm.ruleType,
      reason: ruleForm.reason || undefined,
      isActive: ruleForm.isActive ? 1 : 0,
      expiresAt: ruleForm.expiresAt || undefined
    };

    if (ruleForm.id) {
      await updateIpRule(ruleForm.id, data);
      message("更新成功", { type: "success" });
    } else {
      await createIpRule(data);
      message("新增成功", { type: "success" });
    }
    dialogVisible.value = false;
    onSearch();
  }

  async function handleDelete(row) {
    await deleteIpRule(row.id);
    message("删除成功", { type: "success" });
    onSearch();
  }

  async function handleUpdateStatus(row) {
    await updateIpRule(row.id, { isActive: row.isActive });
    message("状态更新成功", { type: "success" });
  }

  function handleSelectionChange(val) {
    selectedRows.value = val;
  }

  async function handleBatchDelete() {
    const ids = selectedRows.value.map(item => item.id);
    if (!ids.length) {
      message("请选择要删除的数据", { type: "warning" });
      return;
    }
    await batchDeleteIpRule({ ids });
    message("批量删除成功", { type: "success" });
    selectedRows.value = [];
    onSearch();
  }

  async function handleClear() {
    await clearIpRule();
    message("清空成功", { type: "success" });
    onSearch();
  }

  onMounted(() => {
    onSearch();
  });

  return {
    loading,
    form,
    columns,
    dataList,
    formRef,
    pagination,
    dialogVisible,
    dialogTitle,
    ruleForm,
    onSearch,
    resetForm,
    openDialog,
    handleSubmit,
    handleDelete,
    handleSelectionChange,
    handleBatchDelete,
    handleClear,
    handleSizeChange,
    handleCurrentChange
  };
}
