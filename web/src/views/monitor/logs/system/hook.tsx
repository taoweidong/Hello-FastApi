import dayjs from "dayjs";
import Detail from "./detail.vue";
import { message } from "@/utils/message";
import { addDialog } from "@/components/ReDialog";
import type { PaginationProps } from "@pureadmin/table";
import { type Ref, reactive, ref, onMounted, toRaw } from "vue";
import { useCopyToClipboard } from "@pureadmin/utils";
import { getSystemLogsList, getSystemLogsDetail } from "@/api/system/log";
import Info from "~icons/ri/question-line";

export function useSystemLog(tableRef: Ref) {
  const form = reactive({
    module: "",
    createdTime: ""
  });
  const dataList = ref([]);
  const loading = ref(true);
  const { copied, update } = useCopyToClipboard();

  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });

  const columns: TableColumnList = [
    {
      label: "ID",
      prop: "id",
      minWidth: 90
    },
    {
      label: "所属模块",
      prop: "module",
      minWidth: 100
    },
    {
      headerRenderer: () => (
        <span class="flex-c">
          请求接口
          <iconifyIconOffline
            icon={Info}
            class="ml-1 cursor-help"
            v-tippy={{
              content: "双击下面请求接口进行拷贝"
            }}
          />
        </span>
      ),
      prop: "path",
      minWidth: 140,
      showOverflowTooltip: true
    },
    {
      label: "请求方法",
      prop: "method",
      minWidth: 100
    },
    {
      label: "IP 地址",
      prop: "ipaddress",
      minWidth: 120
    },
    {
      label: "操作系统",
      prop: "system",
      minWidth: 100
    },
    {
      label: "浏览器类型",
      prop: "browser",
      minWidth: 100
    },
    {
      label: "响应码",
      prop: "responseCode",
      minWidth: 80,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={row.responseCode < 400 ? "success" : "danger"}
          effect="plain"
        >
          {row.responseCode}
        </el-tag>
      )
    },
    {
      label: "业务状态码",
      prop: "statusCode",
      minWidth: 90
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 160,
      showOverflowTooltip: true
    },
    {
      label: "请求时间",
      prop: "createdTime",
      minWidth: 180,
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : ""
    },
    {
      label: "操作",
      fixed: "right",
      slot: "operation"
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

  function handleCellDblclick(row: any, { property }: { property: string }) {
    if (property !== "path") return;
    update(row.path);
    copied.value
      ? message(`${row.path} 已拷贝`, { type: "success" })
      : message("拷贝失败", { type: "warning" });
  }

  function onDetail(row) {
    getSystemLogsDetail({ id: row.id }).then(res => {
      addDialog({
        title: "系统日志详情",
        fullscreen: true,
        hideFooter: true,
        contentRenderer: () => Detail,
        props: {
          data: [res]
        }
      });
    });
  }

  async function onSearch() {
    loading.value = true;
    const params: Record<string, any> = {
      pageNum: pagination.currentPage,
      pageSize: pagination.pageSize,
      module: form.module || undefined
    };
    if (form.createdTime && form.createdTime.length === 2) {
      params.createdTime = form.createdTime;
    }
    const { code, data } = await getSystemLogsList(params);
    if (code === 0) {
      dataList.value = data.list;
      pagination.total = data.total;
      pagination.pageSize = data.pageSize;
      pagination.currentPage = data.currentPage;
    }

    setTimeout(() => {
      loading.value = false;
    }, 300);
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    pagination.currentPage = 1;
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
    onSearch,
    onDetail,
    resetForm,
    handleSizeChange,
    handleCellDblclick,
    handleCurrentChange
  };
}
