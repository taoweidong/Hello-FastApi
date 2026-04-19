import dayjs from "dayjs";
import editForm from "../form.vue";
import { message } from "@/utils/message";
import { dictionaryApi } from "@/api/system/dictionary";
import { ElMessageBox } from "element-plus";
import { usePublicHooks } from "@/views/system/hooks";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h, computed } from "vue";
import type { FormItemProps } from "../utils/types";
import { deviceDetection } from "@pureadmin/utils";

export function useDictionary() {
  const form = reactive({
    name: "",
    isActive: null as number | null
  });

  const treeSearchValue = ref("");
  const formRef = ref();
  const allDataList = ref([]);
  const loading = ref(true);
  const treeLoading = ref(true);
  const { switchStyle } = usePublicHooks();

  /** 根节点列表（左侧树数据） */
  const dictTypeList = computed(() => {
    return allDataList.value.filter(
      item => !item.parentId || item.parentId === "0" || item.parentId === 0
    );
  });

  /** 当前选中的字典类型 */
  const selectedDictType = ref<any>(null);

  /** 右侧子项数据 */
  const childDataList = computed(() => {
    if (!selectedDictType.value) return [];
    return allDataList.value.filter(
      item => item.parentId === selectedDictType.value.id
    );
  });

  /** 右侧表格列 */
  const columns: TableColumnList = [
    { label: "字典标签", prop: "label", minWidth: 120 },
    { label: "字典值", prop: "value", minWidth: 100 },
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
    { label: "排序", prop: "sort", minWidth: 70 },
    {
      label: "备注",
      prop: "description",
      minWidth: 160,
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
    { label: "操作", fixed: "right", width: 160, slot: "operation" }
  ];

  /** 更新字典项状态 */
  async function handleUpdateStatus(row) {
    const { code } = await dictionaryApi.partialUpdate(row.id, {
      isActive: row.isActive
    });
    if (code === 0) {
      message(`字典 ${row.label} 状态已更新`, { type: "success" });
    } else {
      row.isActive = row.isActive === 1 ? 0 : 1;
    }
  }

  function handleSelectionChange(val) {
    console.log("handleSelectionChange", val);
  }

  function resetForm(formEl) {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  }

  async function onSearch() {
    loading.value = true;
    treeLoading.value = true;
    const { code, data } = await dictionaryApi.list();
    if (code === 0) {
      allDataList.value = data;
      // 默认选中第一个根节点
      if (dictTypeList.value.length > 0 && !selectedDictType.value) {
        selectedDictType.value = dictTypeList.value[0];
      }
    }
    setTimeout(() => {
      loading.value = false;
      treeLoading.value = false;
    }, 300);
  }

  /** 点击左侧树节点 */
  function handleNodeClick(data) {
    selectedDictType.value = data;
  }

  /** 新增子典（根级字典类型） */
  function openAddDictType() {
    addDialog({
      title: "新增字典类型",
      props: {
        formInline: {
          higherDictOptions: [],
          parentId: 0,
          name: "",
          label: "",
          value: "",
          sort: null,
          isActive: 1,
          description: ""
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
                name: curData.name,
                label: curData.label || "",
                value: curData.value || "",
                parentId: 0,
                sort: curData.sort || null,
                isActive: curData.isActive,
                description: curData.description || null
              };

              const { code } = await dictionaryApi.create(payload);
              if (code === 0 || code === 201) {
                message(`成功创建字典类型 ${curData.name}`, {
                  type: "success"
                });
                done();
                onSearch();
              }
            } catch {
              message("新增字典类型失败", { type: "error" });
            }
          }
        });
      }
    });
  }

  /** 新增字典详情（子项） */
  function openAddDictDetail() {
    if (!selectedDictType.value) {
      message("请先选择左侧字典类型", { type: "warning" });
      return;
    }
    addDialog({
      title: "新增字典详情",
      props: {
        formInline: {
          higherDictOptions: [],
          parentId: selectedDictType.value.id,
          name: selectedDictType.value.name,
          label: "",
          value: "",
          sort: null,
          isActive: 1,
          description: ""
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
                name: curData.name,
                label: curData.label || "",
                value: curData.value || "",
                parentId: curData.parentId,
                sort: curData.sort || null,
                isActive: curData.isActive,
                description: curData.description || null
              };

              const { code } = await dictionaryApi.create(payload);
              if (code === 0 || code === 201) {
                message(`成功创建字典详情 ${curData.label}`, {
                  type: "success"
                });
                done();
                onSearch();
              }
            } catch {
              message("新增字典详情失败", { type: "error" });
            }
          }
        });
      }
    });
  }

  /** 修改字典项 */
  function openDialog(title = "修改", row?: FormItemProps) {
    addDialog({
      title: `${title}字典`,
      props: {
        formInline: {
          higherDictOptions: [],
          parentId: row?.parentId ?? 0,
          name: row?.name ?? "",
          label: row?.label ?? "",
          value: row?.value ?? "",
          sort: row?.sort ?? null,
          isActive: row?.isActive ?? 1,
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
                name: curData.name,
                label: curData.label || "",
                value: curData.value || "",
                parentId: curData.parentId || 0,
                sort: curData.sort || null,
                isActive: curData.isActive,
                description: curData.description || null
              };

              if (title === "新增") {
                const { code } = await dictionaryApi.create(payload);
                if (code === 0 || code === 201) {
                  message(`成功创建字典 ${curData.name}`, {
                    type: "success"
                  });
                  done();
                  onSearch();
                }
              } else {
                const { code } = await dictionaryApi.partialUpdate(
                  row.id,
                  payload
                );
                if (code === 0) {
                  message(`成功更新字典 ${curData.label || curData.name}`, {
                    type: "success"
                  });
                  done();
                  onSearch();
                }
              }
            } catch {
              message(`${title}字典失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  /** 删除字典项 */
  function handleDelete(row) {
    ElMessageBox.confirm(
      `确认要删除字典 <strong style='color:var(--el-color-primary)'>${row.label || row.name}</strong> 吗?`,
      "系统提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
        dangerouslyUseHTMLString: true,
        draggable: true
      }
    )
      .then(async () => {
        const { code } = await dictionaryApi.destroy(row.id);
        if (code === 0) {
          message(`已成功删除字典 ${row.label || row.name}`, {
            type: "success"
          });
          onSearch();
        }
      })
      .catch(() => {});
  }

  /** 删除字典类型（根节点） */
  function handleDeleteType(row) {
    // 检查是否有子项
    const hasChildren = allDataList.value.some(
      item => item.parentId === row.id
    );
    if (hasChildren) {
      message("该字典类型下有子项，请先删除子项", { type: "warning" });
      return;
    }
    ElMessageBox.confirm(
      `确认要删除字典类型 <strong style='color:var(--el-color-primary)'>${row.name}</strong> 吗?`,
      "系统提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
        dangerouslyUseHTMLString: true,
        draggable: true
      }
    )
      .then(async () => {
        const { code } = await dictionaryApi.destroy(row.id);
        if (code === 0) {
          message(`已成功删除字典类型 ${row.name}`, { type: "success" });
          // 重置选中状态
          if (selectedDictType.value?.id === row.id) {
            selectedDictType.value = null;
          }
          onSearch();
        }
      })
      .catch(() => {});
  }

  onMounted(() => {
    onSearch();
  });

  return {
    form,
    loading,
    treeLoading,
    treeSearchValue,
    columns,
    allDataList,
    dictTypeList,
    selectedDictType,
    childDataList,
    onSearch,
    resetForm,
    handleNodeClick,
    openAddDictType,
    openAddDictDetail,
    openDialog,
    handleDelete,
    handleDeleteType,
    handleSelectionChange
  };
}
