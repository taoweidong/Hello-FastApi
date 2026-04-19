import dayjs from "dayjs";
import editForm from "./form.vue";
import { message } from "@/utils/message";
import { usePublicHooks } from "@/views/system/hooks";
import { addDialog } from "@/components/ReDialog";
import {
  getConfigList,
  createConfig,
  updateConfig,
  deleteConfig
} from "@/api/system";
import type { FormItemProps } from "./utils/types";
import { ref, onMounted, reactive, h } from "vue";
import { deviceDetection } from "@pureadmin/utils";

export function useConfig() {
  const loading = ref(true);
  const dataList = ref([]);
  const formRef = ref();
  const totalPage = ref(0);
  const pagination = reactive({
    currentPage: 1,
    pageSize: 10
  });

  const form = reactive({
    key: ""
  });

  const { tagStyle } = usePublicHooks();

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

  async function onSearch() {
    loading.value = true;
    try {
      const { data } = await getConfigList({
        key: form.key || undefined,
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
    form.key = "";
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

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}配置`,
      props: {
        formInline: {
          id: row?.id ?? "",
          key: row?.key ?? "",
          value: row?.value ?? "",
          access: row?.access ?? 0,
          isActive: row?.isActive ?? 1,
          inherit: row?.inherit ?? 0,
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
                key: curData.key,
                value: curData.value,
                access: curData.access,
                isActive: curData.isActive,
                inherit: curData.inherit,
                description: curData.description || undefined
              };

              if (title === "新增") {
                await createConfig(payload);
                message("新增成功", { type: "success" });
              } else {
                await updateConfig(row.id, payload);
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
    await deleteConfig(row.id);
    message("删除成功", { type: "success" });
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
    onSearch,
    resetForm,
    openDialog,
    handleDelete,
    handleSizeChange,
    handleCurrentChange
  };
}
