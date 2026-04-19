import dayjs from "dayjs";
import editForm from "./form.vue";
import { message } from "@/utils/message";
import { usePublicHooks } from "@/views/system/hooks";
import { IPRuleTypeChoices } from "@/views/system/constants";
import { addDialog } from "@/components/ReDialog";
import {
  getIpRuleList,
  createIpRule,
  updateIpRule,
  deleteIpRule,
  batchDeleteIpRule,
  clearIpRule
} from "@/api/system";
import type { FormItemProps } from "./utils/types";
import { ref, onMounted, reactive, h } from "vue";
import { deviceDetection } from "@pureadmin/utils";

export function useIpRule() {
  const loading = ref(true);
  const dataList = ref([]);
  const formRef = ref();
  const selectedRows = ref([]);
  const { tagStyle, switchStyle } = usePublicHooks();

  const form = reactive({
    ruleType: "",
    isActive: ""
  });

  const pagination = reactive({
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

  async function onSearch() {
    loading.value = true;
    try {
      const params: Record<string, any> = {
        pageNum: pagination.currentPage,
        pageSize: pagination.pageSize,
        ruleType: form.ruleType || undefined,
        isActive: form.isActive !== "" ? form.isActive : undefined
      };
      const { code, data } = await getIpRuleList(params);
      if (code === 0) {
        dataList.value = data.list || [];
        pagination.total = data.total;
        pagination.pageSize = data.pageSize;
        pagination.currentPage = data.currentPage;
      }
    } catch {
      dataList.value = [];
    }
    loading.value = false;
  }

  function resetForm(formEl) {
    form.ruleType = "";
    form.isActive = "";
    formEl?.resetFields();
    pagination.currentPage = 1;
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

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}IP规则`,
      props: {
        formInline: {
          id: row?.id ?? "",
          ipAddress: row?.ipAddress ?? "",
          ruleType: row?.ruleType ?? "blacklist",
          reason: row?.reason ?? "",
          isActive: row?.isActive ?? 1,
          expiresAt: row?.expiresAt ?? "",
          description: row?.description ?? ""
        }
      },
      width: "40%",
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
                ipAddress: curData.ipAddress,
                ruleType: curData.ruleType,
                reason: curData.reason || undefined,
                isActive: curData.isActive,
                expiresAt: curData.expiresAt || undefined,
                description: curData.description || undefined
              };

              if (title === "新增") {
                await createIpRule(payload);
                message("新增成功", { type: "success" });
              } else {
                await updateIpRule(row.id, payload);
                message("更新成功", { type: "success" });
              }
              done();
              onSearch();
            } catch (error) {
              message(`${title}失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  async function handleDelete(row) {
    await deleteIpRule(row.id);
    message("删除成功", { type: "success" });
    onSearch();
  }

  async function handleUpdateStatus(row) {
    await updateIpRule(row.id, { isActive: row.isActive });
    message("状态更新成功", { type: "success" });
  }

  function handleSelectionChange(val) {
    selectedRows.value = val;
  }

  async function handleBatchDelete() {
    const ids = selectedRows.value.map(item => item.id);
    if (!ids.length) {
      message("请选择要删除的数据", { type: "warning" });
      return;
    }
    await batchDeleteIpRule({ ids });
    message("批量删除成功", { type: "success" });
    selectedRows.value = [];
    onSearch();
  }

  async function handleClear() {
    await clearIpRule();
    message("清空成功", { type: "success" });
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
