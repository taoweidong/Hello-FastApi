import { http } from "@/utils/http";
import type { Result } from "../base";

/** 各实体总数统计 */
export type DashboardTotals = {
  /** 用户总数 */
  users: number;
  /** 角色总数 */
  roles: number;
  /** 菜单总数 */
  menus: number;
  /** 部门总数 */
  depts: number;
  /** 岗位总数 */
  posts: number;
  /** 当前在线人数 */
  online: number;
};

/** 今日累计统计 */
export type DashboardTodayStats = {
  /** 今日登录次数 */
  loginCount: number;
  /** 今日操作次数 */
  opCount: number;
};

/** 登录趋势条目（近 7 天，date 为 "MM-DD" 格式，升序，可能含 0） */
export type LoginTrendItem = {
  date: string;
  count: number;
};

/** 操作模块分布条目（TOP8，按次数降序） */
export type OpDistItem = {
  /** 模块名 */
  module: string;
  /** 操作次数 */
  count: number;
};

/** 最近操作日志条目（仪表盘精简版） */
export type RecentLogItem = {
  id: string;
  /** 所属模块 */
  module: string;
  /** 请求方法（GET/POST/PUT/DELETE 等） */
  method: string;
  /** 请求路径 */
  path: string;
  /** 操作 IP */
  ipaddress: string;
  /** 操作人 */
  creator: string;
  /** 响应状态码，后端异常时可能为 null */
  statusCode: number | null;
  /** 操作时间 */
  createdTime: string;
};

/** 仪表盘聚合统计数据（GET /dashboard/stats 的 data 结构） */
export type DashboardStats = {
  totals: DashboardTotals;
  todayStats: DashboardTodayStats;
  loginTrend: Array<LoginTrendItem>;
  opDistribution: Array<OpDistItem>;
  recentLogs: Array<RecentLogItem>;
};

/** 获取仪表盘聚合统计（总数 / 今日统计 / 登录趋势 / 操作分布 / 最近日志） */
export const getDashboardStats = () =>
  http.request<Result<DashboardStats>>("get", "/dashboard/stats");
