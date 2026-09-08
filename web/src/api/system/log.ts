import { http } from "@/utils/http";
import type { Result, ResultTable } from "../base";
import type { LoginLog, OnlineUser, OperationLog, SystemLog } from "../types";

/** 日志列表查询参数（分页 + 可选筛选） */
export type LogQueryParams = {
  pageNum?: number;
  pageSize?: number;
  [key: string]: unknown;
};

/** 批量删除请求体 */
export type BatchDeletePayload = { ids: Array<string> };

/** 获取在线用户列表 */
export const getOnlineLogsList = (data?: LogQueryParams) => {
  return http.request<ResultTable<OnlineUser>>("post", "/online-logs", {
    data
  });
};

/** 强制下线 */
export const forceOffline = (data: { id?: string; userId?: string }) => {
  return http.request<Result>("post", "/online-logs/force-offline", { data });
};

/** 获取登录日志列表 */
export const getLoginLogsList = (data?: LogQueryParams) => {
  return http.request<ResultTable<LoginLog>>("post", "/login-logs", { data });
};

/** 批量删除登录日志 */
export const batchDeleteLoginLogs = (data: BatchDeletePayload) => {
  return http.request<Result>("post", "/login-logs/batch-delete", { data });
};

/** 清空登录日志 */
export const clearLoginLogs = () => {
  return http.request<Result>("post", "/login-logs/clear");
};

/** 获取操作日志列表 */
export const getOperationLogsList = (data?: LogQueryParams) => {
  return http.request<ResultTable<OperationLog>>("post", "/operation-logs", {
    data
  });
};

/** 批量删除操作日志 */
export const batchDeleteOperationLogs = (data: BatchDeletePayload) => {
  return http.request<Result>("post", "/operation-logs/batch-delete", { data });
};

/** 清空操作日志 */
export const clearOperationLogs = () => {
  return http.request<Result>("post", "/operation-logs/clear");
};

/** 获取系统日志列表 */
export const getSystemLogsList = (data?: LogQueryParams) => {
  return http.request<ResultTable<SystemLog>>("post", "/system-logs", { data });
};

/** 获取系统日志详情 */
export const getSystemLogsDetail = (data: { id: string }) => {
  return http.request<Result<SystemLog>>("post", "/system-logs-detail", {
    data
  });
};

/** 获取我的安全日志 */
export const getMineLogs = (data?: LogQueryParams) => {
  return http.request<ResultTable<LoginLog>>("get", "/mine-logs", { data });
};
