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
