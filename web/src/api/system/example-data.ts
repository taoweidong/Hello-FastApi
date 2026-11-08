import { http } from "@/utils/http";
import type { Result, ResultTable } from "../base";

/** 示例数据行（Univer 表格 CRUD 示例） */
export type ExampleData = {
  id: string;
  /** 名称（必填） */
  name: string;
  category?: string | null;
  quantity: number;
  price: number;
  /** ISO 日期字符串或 null */
  recordDate?: string | null;
  note?: string | null;
  isActive: number;
  creatorId?: string | null;
  createdTime?: string | null;
  updatedTime?: string | null;
};

export type ExampleDataCreatePayload = Omit<
  ExampleData,
  "id" | "creatorId" | "createdTime" | "updatedTime"
>;

export type ExampleDataUpdatePayload = Omit<
  ExampleData,
  "creatorId" | "createdTime" | "updatedTime"
>;

/** Univer 差异回写载荷 */
export type ExampleBatchSavePayload = {
  creates: Array<
    Omit<ExampleDataCreatePayload, "isActive"> & { isActive?: number }
  >;
  updates: ExampleDataUpdatePayload[];
  deletes: string[];
};

export type ExampleBatchSaveResult = {
  created: number;
  updated: number;
  deleted: number;
};

/** 分页列表（Univer 页面以大 pageSize 拉全量） */
export const getExampleRows = (data?: {
  pageNum?: number;
  pageSize?: number;
  name?: string;
  category?: string;
  isActive?: number;
}) => http.request<ResultTable<ExampleData>>("post", "/example-data", { data });

/** 按 ID 获取 */
export const getExampleRow = (id: string) =>
  http.request<Result<ExampleData>>("get", `/example-data/${id}`);

/** 创建单行 */
export const createExampleRow = (data: ExampleDataCreatePayload) =>
  http.request<Result<ExampleData>>("post", "/example-data/create", { data });

/** 更新单行（全行回写） */
export const updateExampleRow = (id: string, data: ExampleDataUpdatePayload) =>
  http.request<Result<ExampleData>>("put", `/example-data/${id}`, { data });

/** 删除单行 */
export const deleteExampleRow = (id: string) =>
  http.request<Result<void>>("delete", `/example-data/${id}`);

/** 批量删除 */
export const batchDeleteExampleRows = (ids: string[]) =>
  http.request<Result<{ deleted: number }>>(
    "post",
    "/example-data/batch-delete",
    {
      data: ids
    }
  );

/** 批量保存（Univer 差异回写：creates + updates + deletes 单事务） */
export const batchSaveExampleRows = (data: ExampleBatchSavePayload) =>
  http.request<Result<ExampleBatchSaveResult>>(
    "post",
    "/example-data/batch-save",
    {
      data
    }
  );
