import dayjs from "dayjs";
import editForm from "../form.vue";
import { handleTree } from "@/utils/tree";
import { message } from "@/utils/message";
import { menuApi } from "@/api/system/menu";
import { ElMessageBox } from "element-plus";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h } from "vue";
import type { FormItemProps } from "../utils/types";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { cloneDeep, isAllEmpty, deviceDetection } from "@pureadmin/utils";
import { formatHigherMenuOptions, getMenuType } from "../../hooks";
import { usePublicHooks } from "../../hooks";

export function useMenu() {
  const form = reactive({
    title: ""
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const { switchStyle } = usePublicHooks();

  const columns: TableColumnList = [
    {
      label: "菜单名称",
      prop: "title",
      align: "left",
      cellRenderer: ({ row }) => (
        <>
          <span class="inline-block mr-1">
            {row.meta?.icon
              ? h(useRenderIcon(row.meta.icon), {
                  style: { paddingTop: "1px" }
                })
              : null}
          </span>
          <span>{row.meta?.title ?? row.name}</span>
        </>
      )
    },
    {
      label: "菜单类型",
      prop: "menuType",
      width: 100,
      cellRenderer: ({ row, props }) => (
        <el-tag
          size={props.size}
          type={getMenuType(row.menuType)}
          effect="plain"
        >
          {getMenuType(row.menuType, true)}
        </el-tag>
      )
    },
    {
      label: "路由路径",
      prop: "path"
    },
    {
      label: "组件路径",
      prop: "component",
      formatter: ({ path, component }) =>
        isAllEmpty(component) ? path : component
    },
    {
      label: "排序",
      prop: "rank",
      width: 100
    },
    {
      label: "显示",
      prop: "isShowMenu",
      cellRenderer: ({ row }) =>
        row.meta?.isShowMenu === false ? "隐藏" : "显示",
      width: 100
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
        />
      )
    },
    {
      label: "创建时间",
      prop: "createdTime",
      minWidth: 160,
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
    const { code, data } = await menuApi.list();
    if (code === 0) {
      let newData = data;
      if (!isAllEmpty(form.title)) {
        newData = newData.filter(item =>
          (item.meta?.title ?? item.name).includes(form.title)
        );
      }
      dataList.value = handleTree(newData);
    }

    setTimeout(() => {
      loading.value = false;
    }, 500);
  }

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}菜单`,
      props: {
        formInline: {
          menuType: row?.menuType ?? 0,
          higherMenuOptions: formatHigherMenuOptions(cloneDeep(dataList.value)),
          parentId: row?.parentId ?? 0,
          name: row?.name ?? "",
          path: row?.path ?? "",
          component: row?.component ?? "",
          rank: row?.rank ?? 99,
          isActive: row?.isActive ?? 1,
          meta: {
            title: row?.meta?.title ?? "",
            icon: row?.meta?.icon ?? "",
            rSvgName: row?.meta?.rSvgName ?? "",
            isShowMenu: row?.meta?.isShowMenu ?? true,
            isShowParent: row?.meta?.isShowParent ?? false,
            isKeepalive: row?.meta?.isKeepalive ?? true,
            frameUrl: row?.meta?.frameUrl ?? "",
            frameLoading: row?.meta?.frameLoading ?? true,
            transitionEnter: row?.meta?.transitionEnter ?? "",
            transitionLeave: row?.meta?.transitionLeave ?? "",
            isHiddenTag: row?.meta?.isHiddenTag ?? false,
            fixedTag: row?.meta?.fixedTag ?? false,
            dynamicLevel: row?.meta?.dynamicLevel ?? null
          }
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
                parentId: curData.parentId || 0,
                menuType: curData.menuType ?? 0,
                name: curData.name || null,
                path: curData.path || null,
                component: curData.component || null,
                rank: curData.rank || 99,
                isActive: curData.isActive ?? 1,
                meta: {
                  title: curData.meta?.title || null,
                  icon: curData.meta?.icon || null,
                  rSvgName: curData.meta?.rSvgName || null,
                  isShowMenu: curData.meta?.isShowMenu ?? true,
                  isShowParent: curData.meta?.isShowParent ?? false,
                  isKeepalive: curData.meta?.isKeepalive ?? true,
                  frameUrl: curData.meta?.frameUrl || null,
                  frameLoading: curData.meta?.frameLoading ?? true,
                  transitionEnter: curData.meta?.transitionEnter || null,
                  transitionLeave: curData.meta?.transitionLeave || null,
                  isHiddenTag: curData.meta?.isHiddenTag ?? false,
                  fixedTag: curData.meta?.fixedTag ?? false,
                  dynamicLevel: curData.meta?.dynamicLevel || null
                }
              };

              if (title === "新增") {
                const { code } = await menuApi.create(payload);
                if (code === 0 || code === 201) {
                  message(
                    `成功创建菜单 ${curData.meta?.title ?? curData.name}`,
                    { type: "success" }
                  );
                  done();
                  onSearch();
                }
              } else {
                const { code } = await menuApi.partialUpdate(row.id, payload);
                if (code === 0) {
                  message(
                    `成功更新菜单 ${curData.meta?.title ?? curData.name}`,
                    { type: "success" }
                  );
                  done();
                  onSearch();
                }
              }
            } catch {
              message(`${title}菜单失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  function handleDelete(row) {
    ElMessageBox.confirm(
      `确认要删除菜单 <strong style='color:var(--el-color-primary)'>${row.meta?.title ?? row.name}</strong> 吗?`,
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
        const { code } = await menuApi.destroy(row.id);
        if (code === 0) {
          message(`已成功删除菜单 ${row.meta?.title ?? row.name}`, {
            type: "success"
          });
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
