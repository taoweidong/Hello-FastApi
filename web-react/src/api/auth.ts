import { http, request } from "./client";
import type { LoginResult } from "@/store/auth";

export async function login(data: { username: string; password: string }): Promise<LoginResult> {
  return request<LoginResult>({ method: "post", url: "/login", data });
}

/** 登出：吊销双令牌。令牌已过期时后端返回 401，可静默忽略（本地状态照常清理） */
export async function logout(refreshToken: string): Promise<void> {
  try {
    await http.post("/logout", { refreshToken });
  } catch {
    /* 已登出/令牌失效：静默忽略 */
  }
}

/** 动态路由树（与 Vue 版同一端点；component 字段为 Vue 视图路径，React 按 path 映射页面） */
export interface AsyncRouteNode {
  path: string;
  name: string;
  rank?: number;
  component?: string;
  meta?: {
    title?: string;
    icon?: string;
    showLink?: boolean;
    keepAlive?: boolean;
    auths?: string[];
  };
  children?: AsyncRouteNode[];
}

export async function getAsyncRoutes(): Promise<AsyncRouteNode[]> {
  return request<AsyncRouteNode[]>({ method: "get", url: "/get-async-routes" });
}

/** 当前登录用户信息 */
export interface MineInfo {
  username: string;
  nickname: string;
  avatar: string;
  email: string;
  phone: string;
}

export async function getMine(): Promise<MineInfo> {
  return request<MineInfo>({ method: "get", url: "/mine" });
}
