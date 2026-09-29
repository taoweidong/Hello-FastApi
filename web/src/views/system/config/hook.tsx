import dayjs from "dayjs";
import editForm from "./form.vue";
import { usePublicHooks } from "@/views/system/hooks";
import { useCrudTable, useDialogForm } from "@/composables";
import { systemConfigApi } from "@/api/system/system_config";
import { reactive } from "vue";

export function useConfig() {
  const form = reactive({
    key: ""
  });

  const { tagStyle } = usePublicHooks();

  const {
    loading,
    dataList,
    pagination,
    onSearch,
    resetForm,
    handleDelete,
    handleSizeChange,
    handleCurrentChange
  } = useCrudTable({
    api: systemConfigApi,
    searchForm: form,
    displayField: "key",
    entityName: "配置"
  });

  const { openDialog } = useDialogForm({
    formComponent: editForm,
    entityName: "配置",
    api: systemConfigApi,
    fieldMappings: [
      { key: "key", defaultValue: "" },
      { key: "value", defaultValue: "" },
      { key: "access", defaultValue: 0 },
      { key: "isActive", defaultValue: 1 },
      { key: "inherit", defaultValue: 0 },
      { key: "description", defaultValue: "", nullable: true }
    ],
    width: "40%",
    onSuccess: onSearch
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
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.isActive)}>
          {row.isActive === 1 ? "启用" : "停用"}
        </el-tag>
      )
    },
    {
      label: "是否继承",
      prop: "inherit",
      minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} type={row.inherit === 1 ? "success" : "info"}>
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
      label: "创建时间",
      prop: "createdTime",
      minWidth: 180,
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "更新时间",
      prop: "updatedTime",
      minWidth: 180,
      formatter: ({ updatedTime }) =>
        updatedTime ? dayjs(updatedTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "操作",
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];

  return {
    loading,
    form,
    columns,
    dataList,
    pagination,
    onSearch,
    resetForm,
    openDialog,
    handleDelete,
    handleSizeChange,
    handleCurrentChange
  };
}
