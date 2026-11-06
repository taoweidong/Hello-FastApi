import { http } from "@/utils/http";
import type { Result } from "../base";

/** 服务器监控数据结构 */
export type ServerInfo = {
  cpu: {
    coreCount: number;
    usedPercent: number;
  };
  memory: {
    total: string;
    used: string;
    free: string;
    usedPercent: number;
  };
  disk: {
    total: string;
    used: string;
    free: string;
    usedPercent: number;
  };
  system: {
    hostname: string;
    osName: string;
    osArch: string;
    pythonVersion: string;
    workDir: string;
    bootTime: string;
  };
  process: {
    pid: number;
    memoryUsed: string;
    cpuPercent: number;
    runningTime: string;
  };
};

/** 缓存监控命令统计条目 */
export type CacheCommandStat = {
  name: string;
  calls: number;
  usec: number;
};

/** 缓存监控数据结构（Redis 不可用时 connected=false 降级） */
export type CacheInfo = {
  connected: boolean;
  message: string;
  version?: string;
  mode?: string;
  uptimeSeconds?: number;
  usedMemory?: string;
  usedMemoryPeak?: string;
  keyCount?: number;
  hitRate?: number;
  clients?: number;
  commandStats: Array<CacheCommandStat>;
};

/** 获取服务器监控数据（CPU/内存/磁盘/系统/进程） */
export const getServerInfo = () =>
  http.request<Result<ServerInfo>>("get", "/server-info");

/** 获取缓存监控数据（Redis info + 键统计） */
export const getCacheInfo = () =>
  http.request<Result<CacheInfo>>("get", "/cache-info");

/** 缓存分组清单条目 */
export type CacheGroup = {
  /** 分组标识（清理接口的入参） */
  key: string;
  /** 分组中文名 */
  name: string;
  /** 键前缀 */
  prefix: string;
  /** 当前键数量 */
  count: number;
  /** 是否允许清理（令牌黑名单为安全红线不可清理） */
  clearable: boolean;
};

/** 缓存清理结果 */
export type CacheClearResult = {
  group: string;
  deleted: number;
};

/** 获取缓存分组清单（各业务缓存分组的键数量） */
export const getCacheGroups = () =>
  http.request<Result<CacheGroup[]>>("get", "/cache-groups");

/** 清理指定分组缓存（仅管理员） */
export const clearCacheGroup = (group: string) =>
  http.request<Result<CacheClearResult>>("post", "/cache-clear", {
    data: { group }
  });

/** 清空全部可清理业务缓存（仅管理员；不含令牌黑名单与限流计数键） */
export const clearAllCache = () =>
  http.request<Result<CacheClearResult>>("post", "/cache-clear-all");

/** 日志文件清单条目 */
export type LogFileInfo = {
  /** 文件名 */
  name: string;
  /** 文件大小（字节） */
  sizeBytes: number;
  /** 最后修改时间（本地时间字符串） */
  modifiedTime: string;
};

/** 日志尾部内容 */
export type LogTail = {
  name: string;
  lines: number;
  content: string;
};

/** 获取日志文件清单（仅管理员） */
export const getLogFiles = () =>
  http.request<Result<LogFileInfo[]>>("get", "/log-files");

/** 读取日志文件末尾 N 行（仅管理员） */
export const tailLogFile = (filename: string, lines = 200) =>
  http.request<Result<LogTail>>(
    "get",
    `/log-files/${encodeURIComponent(filename)}/tail`,
    { params: { lines } }
  );

/** 下载日志文件（仅管理员；blob 由调用方触发保存） */
export const downloadLogFile = (filename: string) =>
  http.request<Blob>("get", `/log-files/${encodeURIComponent(filename)}`, {
    params: { download: true },
    responseType: "blob"
  });
