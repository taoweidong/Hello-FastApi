import { http } from "@/utils/http";
import type {
  LoginLog,
  OnlineUser,
  OperationLog,
  SystemConfig,
  SystemDept,
  SystemDictionary,
  SystemLog,
  SystemMenu,
  SystemNotice,
  SystemRole,
  SystemUser
} from "./types";

/** 通用分页结果类型 */
export type ResultTable<T> = {
  code: number;
  message: string;
  data?: {
    list: Array<T>;
    total?: number;
    pageSize?: number;
    currentPage?: number;
  };
};

/** 通用结果类型 */
export type Result<T = void> = {
  code: number;
  message: string;
  data?: T;
};

/** 分页查询参数 */
export type PageParams = {
  pageNum?: number;
  pageSize?: number;
  [key: string]: unknown;
};

/** 创建/更新请求体（弱约束，允许各模块自定义 payload） */
export type Payload = Record<string, unknown>;

/** 列表页行数据的联合类型，供无泛型场景（如 useCrudTable 的默认参数）使用 */
export type AnyRow =
  | SystemUser
  | SystemRole
  | SystemMenu
  | SystemDept
  | SystemDictionary
  | SystemConfig
  | LoginLog
  | OperationLog
  | SystemLog
  | SystemNotice
  | OnlineUser;

/**
 * BaseApi - 通用 CRUD API 基础类
 *
 * 提供标准的 list / retrieve / create / partialUpdate / destroy 方法，
 * 子类继承后可按需覆写或扩展。
 *
 * 泛型参数：
 * - `TList`：列表项类型
 * - `TDetail`：详情类型，默认与列表项一致
 * - `TPayload`：创建请求体类型；更新请求体自动推导为 `Partial<TPayload>`
 *
 * 通过类级泛型替代原先的方法级 `<T = any>`，使返回值具备真实类型，
 * 调用端不再退化为 any。
 */
export class BaseApi<TList = AnyRow, TDetail = TList, TPayload = Payload> {
  /** API 前缀路径，如 "/user"、"/role" */
  protected readonly prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  /** 获取列表（分页） */
  list(params?: PageParams): Promise<ResultTable<TList>> {
    return http.request<ResultTable<TList>>("post", this.prefix, {
      data: params
    });
  }

  /** 获取详情 */
  retrieve(id: string): Promise<Result<TDetail>> {
    return http.request<Result<TDetail>>("get", `${this.prefix}/${id}`);
  }

  /**
   * 获取树形列表（不分页，data 直接为数组）
   *
   * 部门/菜单/字典等非分页树形接口覆写此方法，与分页的 list() 明确区分，
   * 避免同一方法在不同实现下返回两种截然不同的响应结构。
   */
  listTree(params?: Record<string, unknown>): Promise<Result<TList[]>> {
    return http.request<Result<TList[]>>("post", this.prefix, { data: params });
  }

  /** 创建 */
  create(data: TPayload): Promise<Result<TDetail>> {
    return http.request<Result<TDetail>>("post", `${this.prefix}/create`, {
      data
    });
  }

  /** 更新（全量/部分） */
  partialUpdate(id: string, data: Partial<TPayload>): Promise<Result<TDetail>> {
    return http.request<Result<TDetail>>("put", `${this.prefix}/${id}`, {
      data
    });
  }

  /** 删除 */
  destroy(id: string): Promise<Result> {
    return http.request<Result>("delete", `${this.prefix}/${id}`);
  }

  /** 批量删除 */
  batchDelete(ids: Array<string>): Promise<Result> {
    return http.request<Result>("post", `${this.prefix}/batch-delete`, {
      data: { ids }
    });
  }

  /** 修改状态 */
  updateStatus(id: string, data: Payload): Promise<Result> {
    return http.request<Result>("put", `${this.prefix}/${id}/status`, {
      data
    });
  }
}
