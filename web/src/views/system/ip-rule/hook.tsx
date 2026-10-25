import dayjs from "dayjs";
import editForm from "./form.vue";
import { ElMessageBox } from "element-plus";
import { message } from "@/utils/message";
import { usePublicHooks } from "@/views/system/hooks";
import { IPRuleTypeChoices } from "@/views/system/constants";
import { useCrudTable, useDialogForm } from "@/composables";
import { ipRuleApi } from "@/api/system/ip_rule";
import { ref, reactive } from "vue";

export function useIpRule() {
  const selectedIds = ref<string[]>([]);
  const { switchStyle } = usePublicHooks();

  const form = reactive({
    ruleType: "",
    isActive: ""
  });

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
    api: ipRuleApi,
    searchForm: form,
    displayField: "ipAddress",
    entityName: "IP规则"
  });

  const { openDialog } = useDialogForm({
    formComponent: editForm,
    entityName: "IP规则",
    api: ipRuleApi,
    fieldMappings: [
      { key: "ipAddress", defaultValue: "" },
      { key: "ruleType", defaultValue: "blacklist" },
      { key: "reason", defaultValue: "", nullable: true },
      { key: "isActive", defaultValue: 1 },
      { key: "expiresAt", defaultValue: "", nullable: true },
      { key: "description", defaultValue: "", nullable: true }
    ],
    width: "40%",
    onSuccess: onSearch
  });

  const columns: TableColumnList = [
    {
      label: "勾选列",
      type: "selection",
      fixed: "left",
      reserveSelection: true
    },
    {
      label: "IP地址",
      prop: "ipAddress",
      minWidth: 150
    },
    {
      label: "规则类型",
      prop: "ruleType",
      minWidth: 100,
      cellRenderer: ({ row }) => {
        const choice = IPRuleTypeChoices.find(c => c.value === row.ruleType);
        return (
          <el-tag type={row.ruleType === "whitelist" ? "success" : "danger"}>
            {choice?.label ?? row.ruleType}
          </el-tag>
        );
      }
    },
    {
      label: "原因",
      prop: "reason",
      minWidth: 200,
      showOverflowTooltip: true
    },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-switch
          size={props.size}
          v-model={row.isActive}
          active-value={1}
          inactive-value={0}
          inline-prompt
          active-text="启用"
          inactive-text="停用"
          style={switchStyle.value}
          onChange={() => handleUpdateStatus(row)}
        />
      )
    },
    {
      label: "过期时间",
      prop: "expiresAt",
      minWidth: 180,
      formatter: ({ expiresAt }) =>
        expiresAt ? dayjs(expiresAt).format("YYYY-MM-DD HH:mm:ss") : "永不过期"
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

  async function handleUpdateStatus(row) {
    await ipRuleApi.partialUpdate(row.id, { isActive: row.isActive });
    message("状态更新成功", { type: "success" });
  }

  function handleSelectionChange(val) {
    selectedIds.value = val.map(item => item.id);
  }

  /** 工具栏批量删除按钮，删除当前勾选的 IP 规则 */
  function handleBatchDelete() {
    if (!selectedIds.value.length) {
      return;
    }
    return batchDeleteRows(selectedIds.value);
  }

  /**
   * 清空全部：不可逆的破坏性操作，必须先二次确认。
   * 此前直接调用接口，误点即全量删除且无任何反馈。
   */
  async function handleClear() {
    try {
      await ElMessageBox.confirm(
        "将删除全部 IP 规则（含黑名单与白名单），操作不可恢复。是否继续？",
        "清空全部 IP 规则",
        {
          type: "warning",
          confirmButtonText: "确认清空",
          cancelButtonText: "取消",
          confirmButtonClass: "el-button--danger"
        }
      );
    } catch {
      return; // 用户取消
    }
    try {
      await ipRuleApi.clear();
      message("清空成功", { type: "success" });
      onSearch();
    } catch {
      message("清空失败，请重试", { type: "error" });
    }
  }

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
    handleSelectionChange,
    handleBatchDelete,
    handleClear,
    handleSizeChange,
    handleCurrentChange
  };
}
