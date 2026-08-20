import dayjs from "dayjs";
import editForm from "./form.vue";
import { message } from "@/utils/message";
import { useDict, dictLabel } from "@/composables/useDict";
import { usePublicHooks } from "@/views/system/hooks";
import { addDialog } from "@/components/ReDialog";
import {
  getNoticeList,
  createNotice,
  updateNotice,
  deleteNotice,
  batchDeleteNotice,
  getNotice
} from "@/api/system";
import type { FormItemProps } from "./utils/types";
import { ref, onMounted, reactive, h } from "vue";
import { deviceDetection } from "@pureadmin/utils";

/** 公告类型静态回退选项（字典缺失时兜底） */
const noticeTypeFallback = [
  { label: "通知", value: "1" },
  { label: "公告", value: "2" }
];

export function useNotice() {
  const loading = ref(true);
  const dataList = ref([]);
  const formRef = ref();
  const totalPage = ref(0);
  const selectedIds = ref<string[]>([]);
  const pagination = reactive({
    currentPage: 1,
    pageSize: 10
  });

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

  async function onSearch() {
    loading.value = true;
    try {
      const { data } = await getNoticeList({
        title: form.title || undefined,
        noticeType: form.noticeType ?? undefined,
        isActive: form.isActive ?? undefined,
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

  function resetForm(formEl) {
    form.title = "";
    form.noticeType = null;
    form.isActive = null;
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

  function handleSelectionChange(selections) {
    selectedIds.value = selections.map(item => item.id);
  }

  /** 查看公告详情（只读弹窗） */
  async function handleView(row) {
    try {
      const { data } = await getNotice(row.id);
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

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}公告`,
      props: {
        formInline: {
          id: row?.id ?? "",
          title: row?.title ?? "",
          content: row?.content ?? "",
          noticeType: row?.noticeType ?? 1,
          isActive: row?.isActive ?? 1
        }
      },
      width: "45%",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () => h(editForm, { ref: formRef, formInline: null }),
      beforeSure: (done, { options }) => {
        const FormRef = formRef.value.getRef();
        const curData = options.props.formInline as FormItemProps;

        FormRef.validate(async valid => {
          if (valid) {
            try {
              const payload = {
                title: curData.title,
                content: curData.content,
                noticeType: curData.noticeType,
                isActive: curData.isActive
              };

              if (title === "新增") {
                await createNotice(payload);
                message("新增成功", { type: "success" });
              } else {
                await updateNotice(row.id, payload);
                message("更新成功", { type: "success" });
              }
              done();
              onSearch();
            } catch {
              message(`${title}失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  async function handleDelete(row) {
    await deleteNotice(row.id);
    message("删除成功", { type: "success" });
    onSearch();
  }

  async function handleBatchDelete() {
    if (!selectedIds.value.length) {
      message("请先勾选要删除的公告", { type: "warning" });
      return;
    }
    await batchDeleteNotice({ ids: selectedIds.value });
    message("批量删除成功", { type: "success" });
    selectedIds.value = [];
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
    totalPage,
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
