import { ref, onMounted, reactive } from "vue";
import { message } from "@/utils/message";
import {
  getConfigList,
  createConfig,
  updateConfig,
  deleteConfig
} from "@/api/system";
import type { FormInstance } from "element-plus";

export function useConfig() {
  const loading = ref(true);
  const dataList = ref([]);
  const formRef = ref<FormInstance>();
  const totalPage = ref(0);
  const pagination = reactive({
    currentPage: 1,
    pageSize: 10
  });

  const form = reactive({
    key: ""
  });

  const columns: TableColumnList = [
    {
      type: "selection",
      width: 55,
      reserveSelection: true
    },
    {
      label: "配置键",
      prop: "key",
      minWidth: 150
    },
    {
      label: "配置值",
      prop: "value",
      minWidth: 200,
      showOverflowTooltip: true
    },
    {
      label: "访问级别",
      prop: "access",
      minWidth: 100
    },
    {
      label: "是否启用",
      prop: "isActive",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={row.isActive === 1 ? "success" : "danger"}>
          {row.isActive === 1 ? "启用" : "停用"}
        </el-tag>
      )
    },
    {
      label: "是否继承",
      prop: "inherit",
      minWidth: 100,
      cellRenderer: ({ row }) => (
        <el-tag type={row.inherit === 1 ? "success" : "info"}>
          {row.inherit === 1 ? "是" : "否"}
        </el-tag>
      )
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 150,
      showOverflowTooltip: true
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
      const { data } = await getConfigList({
        key: form.key || undefined,
        pageNum: pagination.currentPage,
        pageSize: pagination.pageSize
      });
      dataList.value = data.list || [];
      totalPage.value = data.total || 0;
    } catch {
      dataList.value = [];
    }
    loading.value = false;
  }

  function resetForm(formEl: FormInstance | undefined) {
    form.key = "";
    formEl?.resetFields();
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
    key: "",
    value: "",
    access: 0,
    isActive: true,
    inherit: false,
    description: ""
  });

  function openDialog(title = "新增", row?: any) {
    dialogTitle.value = title;
    if (row) {
      Object.assign(ruleForm, {
        id: row.id,
        key: row.key,
        value: row.value,
        access: row.access,
        isActive: row.isActive === 1,
        inherit: row.inherit === 1,
        description: row.description || ""
      });
    } else {
      Object.assign(ruleForm, {
        id: "",
        key: "",
        value: "",
        access: 0,
        isActive: true,
        inherit: false,
        description: ""
      });
    }
    dialogVisible.value = true;
  }

  async function handleSubmit() {
    const data = {
      key: ruleForm.key,
      value: ruleForm.value,
      access: ruleForm.access,
      isActive: ruleForm.isActive ? 1 : 0,
      inherit: ruleForm.inherit ? 1 : 0,
      description: ruleForm.description || undefined
    };

    if (ruleForm.id) {
      await updateConfig(ruleForm.id, data);
      message("更新成功", { type: "success" });
    } else {
      await createConfig(data);
      message("新增成功", { type: "success" });
    }
    dialogVisible.value = false;
    onSearch();
  }

  async function handleDelete(row) {
    await deleteConfig(row.id);
    message("删除成功", { type: "success" });
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
    totalPage,
    pagination,
    dialogVisible,
    dialogTitle,
    ruleForm,
    onSearch,
    resetForm,
    openDialog,
    handleSubmit,
    handleDelete,
    handleSizeChange,
    handleCurrentChange
  };
}
