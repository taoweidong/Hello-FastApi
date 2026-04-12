import { http } from "@/utils/http";

/** 通用分页结果类型 */
export type ResultTable<T = any> = {
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
export type Result<T = any> = {
  code: number;
  message: string;
  data?: T;
};

/** 分页查询参数 */
export type PageParams = {
  pageNum?: number;
  pageSize?: number;
  [key: string]: any;
};

/**
 * BaseApi - 通用 CRUD API 基础类
 *
 * 提供标准的 list / retrieve / create / partialUpdate / destroy 方法，
 * 子类继承后可按需覆写或扩展。
 */
export class BaseApi {
  /** API 前缀路径，如 "/user"、"/role" */
  protected readonly prefix: string;

  constructor(prefix: string) {
    this.prefix = prefix;
  }

  /** 获取列表（分页） */
  list<T = any>(params?: PageParams): Promise<ResultTable<T>> {
    return http.request<ResultTable<T>>("post", this.prefix, { data: params });
  }

  /** 获取详情 */
  retrieve<T = any>(id: string): Promise<Result<T>> {
    return http.request<Result<T>>("get", `${this.prefix}/${id}`);
  }

  /** 创建 */
  create<T = any>(data: Record<string, any>): Promise<Result<T>> {
    return http.request<Result<T>>("post", `${this.prefix}/create`, { data });
  }

  /** 更新（全量/部分） */
  partialUpdate<T = any>(
    id: string,
    data: Record<string, any>
  ): Promise<Result<T>> {
    return http.request<Result<T>>("put", `${this.prefix}/${id}`, { data });
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
  updateStatus(id: string, data: Record<string, any>): Promise<Result> {
    return http.request<Result>("put", `${this.prefix}/${id}/status`, {
      data
    });
  }
}
