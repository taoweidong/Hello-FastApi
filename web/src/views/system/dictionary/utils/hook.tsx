import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { dictionaryApi } from "@/api/system/dictionary";
import { ElMessageBox } from "element-plus";
import { usePublicHooks, formatHigherDictOptions } from "./hooks";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h } from "vue";
import type { FormItemProps } from "../utils/types";
import { cloneDeep, isAllEmpty, deviceDetection } from "@pureadmin/utils";

export function useDictionary() {
  const form = reactive({
    name: "",
    isActive: null
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const { tagStyle } = usePublicHooks();

  const columns: TableColumnList = [
    { label: "字典名称", prop: "name", width: 180, align: "left" },
    { label: "显示标签", prop: "label", minWidth: 120 },
    { label: "字典值", prop: "value", minWidth: 120 },
    {
      label: "状态",
      prop: "isActive",
      minWidth: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag size={props.size} style={tagStyle.value(row.isActive)}>
          {row.isActive ? "启用" : "停用"}
        </el-tag>
      )
    },
    { label: "排序", prop: "sort", minWidth: 70 },
    {
      label: "创建时间",
      minWidth: 200,
      prop: "createdTime",
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    { label: "描述", prop: "description", minWidth: 200 },
    { label: "操作", fixed: "right", width: 260, slot: "operation" }
  ];

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
    const { code, data } = await dictionaryApi.list();
    if (code === 0) {
      let newData = data;
      if (!isAllEmpty(form.name)) {
        newData = newData.filter(item => item.name.includes(form.name));
      }
      if (!isAllEmpty(form.isActive)) {
        newData = newData.filter(item => item.isActive === form.isActive);
      }
      dataList.value = handleTree(newData);
    }
    setTimeout(() => {
      loading.value = false;
    }, 500);
  }

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}字典`,
      props: {
        formInline: {
          higherDictOptions: formatHigherDictOptions(
            cloneDeep(dataList.value)
          ),
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
                  message(`成功更新字典 ${curData.name}`, {
                    type: "success"
                  });
                  done();
                  onSearch();
                }
              }
            } catch (error) {
              message(`${title}字典失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  function handleDelete(row) {
    ElMessageBox.confirm(
      `确认要删除字典 <strong style='color:var(--el-color-primary)'>${row.name}</strong> 吗?`,
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
          message(`已成功删除字典 ${row.name}`, { type: "success" });
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
    columns,
    dataList,
    onSearch,
    resetForm,
    openDialog,
    handleDelete,
    handleSelectionChange
  };
}
