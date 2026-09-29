import dayjs from "dayjs";
import editForm from "./form.vue";
import { message } from "@/utils/message";
import { useDict, dictLabel } from "@/composables/useDict";
import { usePublicHooks } from "@/views/system/hooks";
import { useCrudTable, useDialogForm } from "@/composables";
import { addDialog } from "@/components/ReDialog";
import { noticeApi } from "@/api/system/notice";
import { ref, reactive } from "vue";
import { deviceDetection } from "@pureadmin/utils";

/** 公告类型静态回退选项（字典缺失时兜底） */
const noticeTypeFallback = [
  { label: "通知", value: "1" },
  { label: "公告", value: "2" }
];

export function useNotice() {
  const selectedIds = ref<string[]>([]);

  const form = reactive({
    title: "",
    noticeType: null as number | null,
    isActive: null as number | null
  });

  const { tagStyle } = usePublicHooks();
  /** 公告类型字典（后端字典取数，未命中时回退静态选项） */
  const dicts = useDict("sys_notice_type");

  const typeOptions = () =>
    dicts["sys_notice_type"].length
      ? dicts["sys_notice_type"]
      : noticeTypeFallback;

  const {
    loading,
    dataList,
    pagination,
    onSearch,
    resetForm,
    handleDelete,
    handleBatchDelete: batchDeleteRows,
    handleSizeChange,
    handleCurrentChange
  } = useCrudTable({
    api: noticeApi,
    searchForm: form,
    displayField: "title",
    entityName: "公告"
  });

  const { openDialog } = useDialogForm({
    formComponent: editForm,
    entityName: "公告",
    api: noticeApi,
    fieldMappings: [
      { key: "title", defaultValue: "" },
      { key: "content", defaultValue: "", nullable: true },
      { key: "noticeType", defaultValue: 1 },
      { key: "isActive", defaultValue: 1 }
    ],
    width: "45%",
    onSuccess: onSearch
  });

  const columns: TableColumnList = [
    {
      type: "selection",
      width: 55,
      reserveSelection: true
    },
    {
      label: "公告标题",
      prop: "title",
      minWidth: 200,
      showOverflowTooltip: true,
      cellRenderer: ({ row }) => (
        <el-button link type="primary" onClick={() => handleView(row)}>
          {row.title}
        </el-button>
      )
    },
    {
      label: "公告类型",
      prop: "noticeType",
      minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={row.noticeType === 2 ? "warning" : "primary"}
          effect="plain"
        >
          {dictLabel(typeOptions(), row.noticeType, "-")}
        </el-tag>
      )
    },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 90,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.isActive)}>
          {row.isActive === 1 ? "正常" : "关闭"}
        </el-tag>
      )
    },
    {
      label: "发布人",
      prop: "publisherName",
      minWidth: 110
    },
    {
      label: "创建时间",
      prop: "createdTime",
      minWidth: 170,
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

  function handleSelectionChange(selections) {
    selectedIds.value = selections.map(item => item.id);
  }

  /** 模板 popconfirm 确认后触发，删除当前勾选的公告 */
  function handleBatchDelete() {
    if (!selectedIds.value.length) {
      return;
    }
    return batchDeleteRows(selectedIds.value);
  }

  /** 查看公告详情（只读弹窗） */
  async function handleView(row) {
    try {
      const { data } = await noticeApi.retrieve(row.id);
      addDialog({
        title: data.title,
        width: "45%",
        draggable: true,
        fullscreen: deviceDetection(),
        fullscreenIcon: true,
        hideFooter: true,
        contentRenderer: () => (
          <div class="notice-detail">
            <div class="notice-detail-meta">
              <el-tag
                size="small"
                type={data.noticeType === 2 ? "warning" : "primary"}
                effect="plain"
              >
                {dictLabel(typeOptions(), data.noticeType, "-")}
              </el-tag>
              <span>发布人：{data.publisherName || "-"}</span>
              <span>
                发布时间：
                {data.createdTime
                  ? dayjs(data.createdTime).format("YYYY-MM-DD HH:mm:ss")
                  : "-"}
              </span>
            </div>
            <div class="notice-detail-content">
              {data.content || "（无内容）"}
            </div>
          </div>
        )
      });
    } catch {
      message("获取公告详情失败", { type: "error" });
    }
  }

  return {
    loading,
    form,
    columns,
    dataList,
    pagination,
    selectedIds,
    typeOptions,
    onSearch,
    resetForm,
    openDialog,
    handleDelete,
    handleBatchDelete,
    handleSelectionChange,
    handleSizeChange,
    handleCurrentChange
  };
}
