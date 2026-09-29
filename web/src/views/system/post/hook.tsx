import dayjs from "dayjs";
import editForm from "./form.vue";
import { usePublicHooks } from "@/views/system/hooks";
import { useCrudTable, useDialogForm } from "@/composables";
import { postApi } from "@/api/system/post";
import { ref, reactive } from "vue";

export function usePost() {
  const selectedIds = ref<string[]>([]);

  const form = reactive({
    postCode: "",
    postName: "",
    isActive: null as number | null
  });

  const { tagStyle } = usePublicHooks();

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
    api: postApi,
    searchForm: form,
    displayField: "postName",
    entityName: "岗位"
  });

  const { openDialog } = useDialogForm({
    formComponent: editForm,
    entityName: "岗位",
    api: postApi,
    fieldMappings: [
      { key: "postCode", defaultValue: "" },
      { key: "postName", defaultValue: "" },
      { key: "postSort", defaultValue: 0 },
      { key: "isActive", defaultValue: 1 },
      { key: "remark", defaultValue: "", nullable: true }
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

  function handleSelectionChange(selections) {
    selectedIds.value = selections.map(item => item.id);
  }

  /** 模板 popconfirm 确认后触发，删除当前勾选的岗位 */
  function handleBatchDelete() {
    if (!selectedIds.value.length) {
      return;
    }
    return batchDeleteRows(selectedIds.value);
  }

  return {
    loading,
    form,
    columns,
    dataList,
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
