import dayjs from "dayjs";
import { message } from "@/utils/message";
import { getKeyList } from "@pureadmin/utils";
import {
  getOperationLogsList,
  batchDeleteOperationLogs,
  clearOperationLogs
} from "@/api/system/log";
import type { PaginationProps } from "@pureadmin/table";
import { type Ref, reactive, ref, onMounted, toRaw } from "vue";

export function useOperationLog(tableRef: Ref) {
  const form = reactive({
    module: "",
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
      label: "勾选列",
      type: "selection",
      fixed: "left",
      reserveSelection: true
    },
    {
      label: "序号",
      type: "index",
      minWidth: 70
    },
    {
      label: "操作人员",
      prop: "creatorId",
      minWidth: 100
    },
    {
      label: "所属模块",
      prop: "module",
      minWidth: 120
    },
        {
      label: "请求地址",
      prop: "path",
      minWidth: 120
    },
    {
      label: "操作概要",
      prop: "description",
      minWidth: 180,
      showOverflowTooltip: true
    },
    {
      label: "操作IP",
      prop: "ipaddress",
      minWidth: 130
    },
    {
      label: "操作地点",
      prop: "location",
      minWidth: 160,
      cellRenderer: () => <span>-</span>
    },
    {
      label: "操作系统",
      prop: "system",
      minWidth: 100
    },
    {
      label: "浏览器类型",
      prop: "browser",
      minWidth: 110
    },
    {
      label: "操作状态",
      prop: "statusCode",
      minWidth: 90,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={row.statusCode === 200 ? "success" : "danger"}
          effect="plain"
        >
          {row.statusCode === 200 ? "成功" : "失败"}
        </el-tag>
      )
    },
    {
      label: "操作时间",
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
    batchDeleteOperationLogs({ ids }).then(res => {
      if (res.code === 0) {
        message(`已删除序号为 ${ids} 的数据`, { type: "success" });
        tableRef.value.getTableRef().clearSelection();
        onSearch();
      }
    });
  }

  function clearAll() {
    clearOperationLogs().then(res => {
      if (res.code === 0) {
        message("已删除所有日志数据", { type: "success" });
        onSearch();
      }
    });
  }

  async function onSearch() {
    loading.value = true;
    const { code, data } = await getOperationLogsList(toRaw(form));
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
