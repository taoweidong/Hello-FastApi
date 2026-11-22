/**
 * useCrudTable - 通用 CRUD 表格核心逻辑
 *
 * 封装分页、搜索、删除等通用操作，减少 hook.tsx 中的重复代码。
 * 支持分页模式（paginated）和树形模式（tree）。
 */
import Axios from "axios";
import { message } from "@/utils/message";
import { handleTree } from "@/utils/tree";
import type { AnyRow, BaseApi, ResultTable } from "@/api/base";
import type { PaginationProps } from "@pureadmin/table";
import {
  reactive,
  ref,
  onMounted,
  onScopeDispose,
  getCurrentScope,
  toRaw,
  type Ref
} from "vue";

/**
 * 判断错误是否属于"全局响应拦截器已统一提示"的网络层错误
 * （取消请求、断网/超时等无响应错误、5xx 服务端错误）。
 * 页面层 catch 命中时应静默（仅复位 loading），避免同一失败弹两层 toast；
 * 返回 false 时为 4xx 等业务错误，由页面本地提示。
 */
export function isNetworkLevelError(error: unknown): boolean {
  if (Axios.isCancel(error)) return true;
  const status = (error as { response?: { status?: number } })?.response
    ?.status;
  return status === undefined || status >= 500;
}

/**
 * 判断错误是否为"请求被取消"（AbortController / axios cancel）。
 * 需先于 isNetworkLevelError 判断：取消属于竞态防护的正常路径，
 * 页面层应完全静默（不提示、不覆盖数据、不碰 loading）。
 */
export function isRequestCanceled(error: unknown): boolean {
  return (
    Axios.isCancel(error) ||
    (error as { code?: string } | null)?.code === "ERR_CANCELED"
  );
}

/** useCrudTable 配置项 */
export interface UseCrudTableOptions<TList> {
  /** BaseApi 实例，如 roleApi、userApi */
  api: BaseApi<TList, TList, Record<string, unknown>>;
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
export interface UseCrudTableReturn<TList> {
  /** 加载状态 */
  loading: Ref<boolean>;
  /** 数据列表 */
  dataList: Ref<TList[]>;
  /** 分页配置 */
  pagination: PaginationProps;
  /** 搜索数据 */
  onSearch: () => Promise<void>;
  /** 重置搜索表单并重新搜索 */
  resetForm: (formEl?: any) => void;
  /** 删除单条数据（确认由页面 popconfirm 负责，这里直接执行删除） */
  handleDelete: (row: TList) => Promise<void>;
  /** 批量删除（确认由页面 popconfirm 负责，这里直接执行删除） */
  handleBatchDelete: (ids: string[]) => Promise<void>;
  /** 每页条数变化 */
  handleSizeChange: (val: number) => void;
  /** 当前页变化 */
  handleCurrentChange: (val: number) => void;
}

/** 移除空字符串与 undefined 的搜索条件，避免后端把 "" 当作有效过滤值 */
function pruneEmpty(obj: Record<string, unknown>) {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value === "" || value === undefined) continue;
    result[key] = value;
  }
  return result;
}

export function useCrudTable<TList extends AnyRow = AnyRow>(
  options: UseCrudTableOptions<TList>
): UseCrudTableReturn<TList> {
  const {
    api,
    searchForm,
    displayField,
    entityName,
    listMode = "paginated",
    immediate = true
  } = options;

  const loading = ref(true);
  const dataList = ref<TList[]>([]) as Ref<TList[]>;
  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });

  /** 当前搜索请求的取消控制器：新搜索发起前 abort 上一次，防止慢响应覆盖新结果 */
  let searchController: AbortController | null = null;

  /** 搜索数据 */
  async function onSearch() {
    // 竞态防护：取消上一次未完成的搜索请求
    searchController?.abort();
    const controller = new AbortController();
    searchController = controller;
    loading.value = true;
    try {
      const { code, data } = await api.list(
        {
          ...pruneEmpty(toRaw(searchForm)),
          pageNum: pagination.currentPage,
          pageSize: pagination.pageSize
        },
        { signal: controller.signal }
      );
      // 已被更新的搜索取代：丢弃过期结果，数据与 loading 交给最新请求
      if (controller.signal.aborted) return;
      if (code === 0 && data) {
        if (listMode === "paginated") {
          const result = data as NonNullable<ResultTable<TList>["data"]>;
          dataList.value = result.list || [];
          pagination.total = result.total ?? 0;
          pagination.pageSize = result.pageSize ?? 10;
          pagination.currentPage = result.currentPage ?? 1;
        } else {
          // 树形模式：data 直接是数组
          dataList.value = handleTree(data as unknown as any[]);
        }
      }
    } catch (error) {
      /*
       * 查询失败时保留原数据，避免表格静默空白让用户误以为是"真的没有数据"。
       * 请求被取消属于竞态防护的正常路径：静默返回，不提示、不覆盖数据，
       * loading 由最新请求接管；断网/5xx 已由全局响应拦截器统一提示，
       * 这里静默复位 loading 即可，仅 4xx 等业务错误做本地提示，避免重复 toast。
       */
      if (isRequestCanceled(error)) return;
      if (!isNetworkLevelError(error)) {
        message(`${entityName}列表加载失败，请稍后重试`, { type: "error" });
      }
    } finally {
      // 仅当本次请求仍是最新搜索时才复位 loading，避免取消旧请求时误关新请求的加载态
      if (searchController === controller) {
        loading.value = false;
      }
    }
  }

  /** 重置搜索表单并重新搜索 */
  function resetForm(formEl?: any) {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  }

  /** 删除单条数据（确认已由页面 popconfirm 完成，这里直接执行删除） */
  async function handleDelete(row: any) {
    try {
      const { code } = await api.destroy(row.id);
      if (code === 0) {
        message(`已成功删除${entityName} ${row[displayField]}`, {
          type: "success"
        });
        // 当前页仅剩这一条且不在首页时页码回退，避免刷新后落在空页
        if (dataList.value.length === 1 && pagination.currentPage > 1) {
          pagination.currentPage -= 1;
        }
        onSearch();
      }
    } catch {
      // 删除请求失败：给出明确提示，用户可重试而不是无感知失败
      message(`删除${entityName}失败，请稍后重试`, { type: "error" });
    }
  }

  /** 批量删除（确认已由页面 popconfirm 完成，这里直接执行删除） */
  async function handleBatchDelete(ids: string[]) {
    try {
      const { code } = await api.batchDelete(ids);
      if (code === 0) {
        message(`已成功删除 ${ids.length} 条${entityName}数据`, {
          type: "success"
        });
        // 当前页数据全部删完且不在首页时页码回退，避免刷新后落在空页
        if (dataList.value.length <= ids.length && pagination.currentPage > 1) {
          pagination.currentPage -= 1;
        }
        onSearch();
      }
    } catch {
      // 删除请求失败：给出明确提示
      message(`批量删除${entityName}失败，请稍后重试`, { type: "error" });
    }
  }

  /** 每页条数变化：改 pageSize 后旧页码可能超出新的总页数，先回到第 1 页再刷新 */
  function handleSizeChange(val: number) {
    pagination.pageSize = val;
    pagination.currentPage = 1;
    onSearch();
  }

  /** 当前页变化 */
  function handleCurrentChange(val: number) {
    pagination.currentPage = val;
    onSearch();
  }

  // 组件卸载时取消进行中的搜索请求，防止卸载后仍回写状态
  // （单测等无组件场景无 effect scope，跳过注册）
  if (getCurrentScope()) {
    onScopeDispose(() => {
      searchController?.abort();
    });
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
