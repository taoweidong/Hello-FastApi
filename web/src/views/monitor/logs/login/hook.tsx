import dayjs from "dayjs";
import { message } from "@/utils/message";
import { getKeyList } from "@pureadmin/utils";
import {
  getLoginLogsList,
  batchDeleteLoginLogs,
  clearLoginLogs
} from "@/api/system/log";
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

  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });

  const columns: TableColumnList = [
    {
      // 勾选列统一宽度 55、无标题文案；本页列较多，保留 fixed:left 防横向滚动丢失勾选
      type: "selection",
      fixed: "left",
      width: 55,
      reserveSelection: true
    },
    {
      label: "序号",
      type: "index",
      minWidth: 70
    },
    {
      label: "登录状态",
      prop: "status",
      minWidth: 100,
      // 状态 tag 统一 EP success/danger 色板（与操作日志等全站状态列一致）
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={row.status === 1 ? "success" : "danger"}
        >
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
    try {
      const { code, data } = await getLoginLogsList({
        ...toRaw(form),
        pageNum: pagination.currentPage,
        pageSize: pagination.pageSize
      });
      if (code === 0) {
        dataList.value = data.list;
        pagination.total = data.total;
        pagination.pageSize = data.pageSize;
        pagination.currentPage = data.currentPage;
      }
    } catch {
      message("登录日志加载失败，请稍后重试", { type: "error" });
    } finally {
      loading.value = false;
    }
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
