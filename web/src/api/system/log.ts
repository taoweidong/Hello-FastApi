import { http } from "@/utils/http";
import { type Result, type ResultTable } from "../base";

/** 获取在线用户列表 */
export const getOnlineLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/online-logs", { data });
};

/** 强制下线 */
export const forceOffline = (data?: object) => {
  return http.request<Result>("post", "/online-logs/force-offline", { data });
};

/** 获取登录日志列表 */
export const getLoginLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/login-logs", { data });
};

/** 批量删除登录日志 */
export const batchDeleteLoginLogs = (data?: object) => {
  return http.request<Result>("post", "/login-logs/batch-delete", { data });
};

/** 清空登录日志 */
export const clearLoginLogs = () => {
  return http.request<Result>("post", "/login-logs/clear");
};

/** 获取操作日志列表 */
export const getOperationLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/operation-logs", { data });
};

/** 批量删除操作日志 */
export const batchDeleteOperationLogs = (data?: object) => {
  return http.request<Result>("post", "/operation-logs/batch-delete", { data });
};

/** 清空操作日志 */
export const clearOperationLogs = () => {
  return http.request<Result>("post", "/operation-logs/clear");
};

/** 获取系统日志列表 */
export const getSystemLogsList = (data?: object) => {
  return http.request<ResultTable>("post", "/system-logs", { data });
};

/** 获取系统日志详情 */
export const getSystemLogsDetail = (data?: object) => {
  return http.request<Result>("post", "/system-logs-detail", { data });
};

/** 获取我的安全日志 */
export const getMineLogs = (data?: object) => {
  return http.request<ResultTable>("get", "/mine-logs", { data });
};
