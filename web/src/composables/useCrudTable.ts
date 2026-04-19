/**
 * useCrudTable - 通用 CRUD 表格核心逻辑
 *
 * 封装分页、搜索、删除等通用操作，减少 hook.tsx 中的重复代码。
 * 支持分页模式（paginated）和树形模式（tree）。
 */
import { message } from "@/utils/message";
import { handleTree } from "@/utils/tree";
import type { BaseApi, ResultTable } from "@/api/base";
import { ElMessageBox } from "element-plus";
import type { PaginationProps } from "@pureadmin/table";
import { reactive, ref, onMounted, toRaw, type Ref } from "vue";

/** useCrudTable 配置项 */
export interface UseCrudTableOptions {
  /** BaseApi 实例，如 roleApi、userApi */
  api: BaseApi;
  /** 搜索表单 reactive 对象 */
  searchForm: Record<string, any>;
  /** 删除确认时显示的字段名，如 "name"、"username" */
  displayField: string;
  /** 实体中文名，如 "角色"、"用户" */
  entityName: string;
  /** 列表模式，默认 paginated */
  listMode?: "paginated" | "tree";
  /** 是否在 onMounted 时自动搜索，默认 true */
  immediate?: boolean;
}

/** useCrudTable 返回值 */
export interface UseCrudTableReturn {
  /** 加载状态 */
  loading: Ref<boolean>;
  /** 数据列表 */
  dataList: Ref<any[]>;
  /** 分页配置 */
  pagination: PaginationProps;
  /** 搜索数据 */
  onSearch: () => Promise<void>;
  /** 重置搜索表单并重新搜索 */
  resetForm: (formEl?: any) => void;
  /** 删除单条数据（含确认弹窗） */
  handleDelete: (row: any) => Promise<void>;
  /** 批量删除（含确认弹窗） */
  handleBatchDelete: (ids: string[]) => Promise<void>;
  /** 每页条数变化 */
  handleSizeChange: (val: number) => void;
  /** 当前页变化 */
  handleCurrentChange: (val: number) => void;
}

export function useCrudTable(options: UseCrudTableOptions): UseCrudTableReturn {
  const {
    api,
    searchForm,
    displayField,
    entityName,
    listMode = "paginated",
    immediate = true
  } = options;

  const loading = ref(true);
  const dataList = ref([]);
  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });

  /** 搜索数据 */
  async function onSearch() {
    loading.value = true;
    try {
      const { code, data } = await api.list(toRaw(searchForm));
      if (code === 0 && data) {
        if (listMode === "paginated") {
          const result = data as NonNullable<ResultTable["data"]>;
          dataList.value = result.list || [];
          pagination.total = result.total ?? 0;
          pagination.pageSize = result.pageSize ?? 10;
          pagination.currentPage = result.currentPage ?? 1;
        } else {
          // 树形模式：data 直接是数组
          dataList.value = handleTree(data as unknown as any[]);
        }
      }
    } catch {
      dataList.value = [];
    } finally {
      loading.value = false;
    }
  }

  /** 重置搜索表单并重新搜索 */
  function resetForm(formEl?: any) {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  }

  /** 删除单条数据 */
  async function handleDelete(row: any) {
    try {
      await ElMessageBox.confirm(
        `确认要删除${entityName} <strong style='color:var(--el-color-primary)'>${row[displayField]}</strong> 吗?`,
        "系统提示",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
          dangerouslyUseHTMLString: true,
          draggable: true
        }
      );
      const { code } = await api.destroy(row.id);
      if (code === 0) {
        message(`已成功删除${entityName} ${row[displayField]}`, {
          type: "success"
        });
        onSearch();
      }
    } catch {
      // 用户取消
    }
  }

  /** 批量删除 */
  async function handleBatchDelete(ids: string[]) {
    try {
      await ElMessageBox.confirm(
        `确认要删除选中的 <strong style='color:var(--el-color-primary)'>${ids.length}</strong> 条${entityName}数据吗?`,
        "系统提示",
        {
          confirmButtonText: "确定",
          cancelButtonText: "取消",
          type: "warning",
          dangerouslyUseHTMLString: true,
          draggable: true
        }
      );
      const { code } = await api.batchDelete(ids);
      if (code === 0) {
        message(`已成功删除 ${ids.length} 条${entityName}数据`, {
          type: "success"
        });
        onSearch();
      }
    } catch {
      // 用户取消
    }
  }

  /** 每页条数变化 */
  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    onSearch();
  }

  /** 当前页变化 */
  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  if (immediate) {
    onMounted(() => {
      onSearch();
    });
  }

  return {
    loading,
    dataList,
    pagination,
    onSearch,
    resetForm,
    handleDelete,
    handleBatchDelete,
    handleSizeChange,
    handleCurrentChange
  };
}
