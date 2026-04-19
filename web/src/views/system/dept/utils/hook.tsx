import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { deptApi } from "@/api/system/dept";
import { ElMessageBox } from "element-plus";
import { usePublicHooks, formatHigherDeptOptions } from "../../hooks";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h } from "vue";
import type { FormItemProps } from "../utils/types";
import { cloneDeep, isAllEmpty, deviceDetection } from "@pureadmin/utils";

export function useDept() {
  const form = reactive({
    name: "",
    isActive: null
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const { tagStyle } = usePublicHooks();

  const columns: TableColumnList = [
    {
      label: "部门名称",
      prop: "name",
      width: 180,
      align: "left"
    },
    {
      label: "部门编码",
      prop: "code",
      minWidth: 120
    },
    {
      label: "负责人",
      prop: "principal",
      minWidth: 100
    },
    {
      label: "联系电话",
      prop: "phone",
      minWidth: 120
    },
    {
      label: "邮箱",
      prop: "email",
      minWidth: 160,
      showOverflowTooltip: true
    },
    {
      label: "排序",
      prop: "rank",
      minWidth: 70
    },
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
    {
      label: "创建时间",
      minWidth: 160,
      prop: "createdTime",
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "更新时间",
      prop: "updatedTime",
      minWidth: 160,
      formatter: ({ updatedTime }) =>
        updatedTime ? dayjs(updatedTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "描述",
      prop: "description",
      minWidth: 200,
      showOverflowTooltip: true
    },
    {
      label: "操作",
      fixed: "right",
      width: 210,
      slot: "operation"
    }
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
    const { code, data } = await deptApi.list();
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
      title: `${title}部门`,
      props: {
        formInline: {
          higherDeptOptions: formatHigherDeptOptions(cloneDeep(dataList.value)),
          parentId: row?.parentId ?? 0,
          name: row?.name ?? "",
          code: row?.code ?? "",
          principal: row?.principal ?? "",
          phone: row?.phone ?? "",
          email: row?.email ?? "",
          rank: row?.rank ?? 0,
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
                code: curData.code || null,
                parentId: curData.parentId || 0,
                rank: curData.rank,
                principal: curData.principal || null,
                phone: curData.phone || null,
                email: curData.email || null,
                isActive: curData.isActive,
                description: curData.description || null
              };
              
              if (title === "新增") {
                const { code } = await deptApi.create(payload);
                if (code === 0 || code === 201) {
                  message(`成功创建部门 ${curData.name}`, { type: "success" });
                  done();
                  onSearch();
                }
              } else {
                const { code } = await deptApi.partialUpdate(row.id, payload);
                if (code === 0) {
                  message(`成功更新部门 ${curData.name}`, { type: "success" });
                  done();
                  onSearch();
                }
              }
            } catch (error) {
              message(`${title}部门失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  function handleDelete(row) {
    ElMessageBox.confirm(
      `确认要删除部门 <strong style='color:var(--el-color-primary)'>${row.name}</strong> 吗?`,
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
        const { code } = await deptApi.destroy(row.id);
        if (code === 0) {
          message(`已成功删除部门 ${row.name}`, { type: "success" });
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
