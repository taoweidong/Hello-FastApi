import dayjs from "dayjs";
import { message } from "@/utils/message";
import { getKeyList } from "@pureadmin/utils";
import { getLoginLogsList, batchDeleteLoginLogs, clearLoginLogs } from "@/api/system/log";
import { usePublicHooks } from "@/views/system/hooks";
import type { PaginationProps } from "@pureadmin/table";
import { type Ref, reactive, ref, onMounted, toRaw } from "vue";

export function useLoginLog(tableRef: Ref) {
  const form = reactive({
    loginType: "",
    status: "",
    createdTime: ""
  });
  const dataList = ref([]);
  const loading = ref(true);
  const selectedNum = ref(0);
  const { tagStyle } = usePublicHooks();

  const pagination = reactive<PaginationProps>({
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
      label: "序号",
      prop: "id",
      minWidth: 90
    },
    {
      label: "登录状态",
      prop: "status",
      minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.status)}>
          {row.status === 1 ? "成功" : "失败"}
        </el-tag>
      )
    },
    {
      label: "登录类型",
      prop: "loginType",
      minWidth: 100,
      cellRenderer: ({ row }) => {
        const typeMap = { 0: "密码", 1: "短信", 2: "OAuth" };
        return typeMap[row.loginType] ?? row.loginType;
      }
    },
    {
      label: "IP地址",
      prop: "ipaddress",
      minWidth: 140
    },
    {
      label: "操作系统",
      prop: "system",
      minWidth: 100
    },
    {
      label: "浏览器",
      prop: "browser",
      minWidth: 100
    },
    {
      label: "User-Agent",
      prop: "agent",
      minWidth: 200,
      showOverflowTooltip: true
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 160,
      showOverflowTooltip: true
    },
    {
      label: "登录时间",
      prop: "createdTime",
      minWidth: 180,
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    }
  ];

  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    onSearch();
  }

  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  function handleSelectionChange(val) {
    selectedNum.value = val.length;
    tableRef.value.setAdaptive();
  }

  function onSelectionCancel() {
    selectedNum.value = 0;
    tableRef.value.getTableRef().clearSelection();
  }

  function onbatchDel() {
    const curSelected = tableRef.value.getTableRef().getSelectionRows();
    const ids = getKeyList(curSelected, "id");
    batchDeleteLoginLogs({ ids }).then(res => {
      if (res.code === 0) {
        message(`已删除序号为 ${ids} 的数据`, { type: "success" });
        tableRef.value.getTableRef().clearSelection();
        onSearch();
      }
    });
  }

  function clearAll() {
    clearLoginLogs().then(res => {
      if (res.code === 0) {
        message("已删除所有日志数据", { type: "success" });
        onSearch();
      }
    });
  }

  async function onSearch() {
    loading.value = true;
    const { code, data } = await getLoginLogsList(toRaw(form));
    if (code === 0) {
      dataList.value = data.list;
      pagination.total = data.total;
      pagination.pageSize = data.pageSize;
      pagination.currentPage = data.currentPage;
    }

    setTimeout(() => {
      loading.value = false;
    }, 500);
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  };

  onMounted(() => {
    onSearch();
  });

  return {
    form,
    loading,
    columns,
    dataList,
    pagination,
    selectedNum,
    onSearch,
    clearAll,
    resetForm,
    onbatchDel,
    handleSizeChange,
    onSelectionCancel,
    handleCurrentChange,
    handleSelectionChange
  };
}
