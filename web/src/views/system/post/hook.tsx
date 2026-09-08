import dayjs from "dayjs";
import editForm from "./form.vue";
import { message } from "@/utils/message";
import { usePublicHooks } from "@/views/system/hooks";
import { addDialog } from "@/components/ReDialog";
import {
  getPostList,
  createPost,
  updatePost,
  deletePost,
  batchDeletePost
} from "@/api/system";
import type { FormItemProps } from "./utils/types";
import { ref, onMounted, reactive, h } from "vue";
import { deviceDetection } from "@pureadmin/utils";

export function usePost() {
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
    postCode: "",
    postName: "",
    isActive: null as number | null
  });

  const { tagStyle } = usePublicHooks();

  const columns: TableColumnList = [
    {
      type: "selection",
      width: 55,
      reserveSelection: true
    },
    {
      label: "岗位编码",
      prop: "postCode",
      minWidth: 120
    },
    {
      label: "岗位名称",
      prop: "postName",
      minWidth: 140
    },
    {
      label: "排序",
      prop: "postSort",
      minWidth: 80
    },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 90,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.isActive)}>
          {row.isActive === 1 ? "正常" : "停用"}
        </el-tag>
      )
    },
    {
      label: "备注",
      prop: "remark",
      minWidth: 160,
      showOverflowTooltip: true
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
      const { data } = await getPostList({
        postCode: form.postCode || undefined,
        postName: form.postName || undefined,
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
    form.postCode = "";
    form.postName = "";
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

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}岗位`,
      props: {
        formInline: {
          id: row?.id ?? "",
          postCode: row?.postCode ?? "",
          postName: row?.postName ?? "",
          postSort: row?.postSort ?? 0,
          isActive: row?.isActive ?? 1,
          remark: row?.remark ?? ""
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
                postCode: curData.postCode,
                postName: curData.postName,
                postSort: curData.postSort,
                isActive: curData.isActive,
                remark: curData.remark
              };

              if (title === "新增") {
                await createPost(payload);
                message("新增成功", { type: "success" });
              } else {
                await updatePost(row.id, payload);
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
    await deletePost(row.id);
    message("删除成功", { type: "success" });
    onSearch();
  }

  async function handleBatchDelete() {
    if (!selectedIds.value.length) {
      message("请先勾选要删除的岗位", { type: "warning" });
      return;
    }
    await batchDeletePost({ ids: selectedIds.value });
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
