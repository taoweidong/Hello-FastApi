/** Hello-FastApi 后端 API 服务层（与 Vue 版 web/src/api/*.ts 对齐） */
import { request } from '@umijs/max';

// ---- 通用响应封装 ----
export interface ApiResponse<T = unknown> {
  code: number;
  message: string;
  data: T;
}

// ---- 认证 ----
export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  expires: string;
  roles: string[];
  permissions: string[];
  username: string;
  nickname: string;
  avatar: string;
}

export async function login(body: { username: string; password: string }): Promise<LoginResult> {
  const res = await request<ApiResponse<LoginResult>>('/api/system/login', {
    method: 'POST',
    data: body,
    skipErrorHandler: true,
  });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function logout(refreshToken: string): Promise<void> {
  try {
    await request('/api/system/logout', { method: 'POST', data: { refreshToken } });
  } catch { /* 静默 */ }
}

export interface MineInfo {
  username: string;
  nickname: string;
  avatar: string;
  email: string;
  phone: string;
}

export async function getMine(): Promise<MineInfo> {
  const res = await request<ApiResponse<MineInfo>>('/api/system/mine');
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

/** 动态路由树 */
export interface AsyncRouteNode {
  path: string;
  name: string;
  rank?: number;
  meta?: {
    title?: string;
    icon?: string;
    showLink?: boolean;
    auths?: string[];
  };
  children?: AsyncRouteNode[];
}

export async function getAsyncRoutes(): Promise<AsyncRouteNode[]> {
  const res = await request<ApiResponse<AsyncRouteNode[]>>('/api/system/get-async-routes');
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

// ---- 用户管理 ----
export interface UserRow {
  id: string;
  username: string;
  nickname: string | null;
  email: string | null;
  phone: string | null;
  isActive: number;
  roles: Array<{ id: string; name: string }>;
  dept: { id: string; name: string } | null;
  createdTime: string | null;
}

export interface UserPage {
  list: UserRow[];
  total: number;
  pageSize: number;
  currentPage: number;
}

export async function getUsers(params: Record<string, unknown>): Promise<UserPage> {
  const res = await request<ApiResponse<UserPage>>('/api/system/user', {
    method: 'POST',
    data: params,
  });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function createUser(data: Record<string, unknown>): Promise<UserRow> {
  const res = await request<ApiResponse<UserRow>>('/api/system/user/create', { method: 'POST', data });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function updateUser(id: string, data: Record<string, unknown>): Promise<UserRow> {
  const res = await request<ApiResponse<UserRow>>(`/api/system/user/${id}`, { method: 'PUT', data });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function deleteUser(id: string): Promise<void> {
  await request(`/api/system/user/${id}`, { method: 'DELETE' });
}

export async function updateUserStatus(id: string, isActive: number): Promise<void> {
  await request(`/api/system/user/${id}/status`, { method: 'PUT', data: { isActive } });
}

export async function assignRoles(userId: string, roleIds: string[]): Promise<void> {
  await request('/api/system/user/assign-role', { method: 'POST', data: { userId, roleIds } });
}

// ---- 角色管理 ----
export interface RoleRow {
  id: string;
  name: string;
  code: string;
  isActive: number;
  dataScope: number;
  description: string | null;
  createdTime: string | null;
}

export interface RolePage {
  list: RoleRow[];
  total: number;
  pageSize: number;
  currentPage: number;
}

export async function getRoles(params: Record<string, unknown>): Promise<RolePage> {
  const res = await request<ApiResponse<RolePage>>('/api/system/role', { method: 'POST', data: params });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function getRoleMenuIds(roleId: string): Promise<string[]> {
  const res = await request<ApiResponse<string[]>>('/api/system/role-menu-ids', { method: 'POST', data: { id: roleId } });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function saveRoleMenu(roleId: string, menuIds: string[]): Promise<void> {
  await request(`/api/system/role/${roleId}/menus`, { method: 'POST', data: { menuIds } });
}

// ---- 通用 CRUD 工厂 ----
export function createCrudService(prefix: string) {
  return {
    list: async (params: Record<string, unknown>) => {
      const res = await request<ApiResponse<{ list: unknown[]; total: number; pageSize: number; currentPage: number }>>(
        `/api/system/${prefix}`,
        { method: 'POST', data: params }
      );
      if (res.code !== 0) throw new Error(res.message);
      return res.data;
    },
    create: async (data: Record<string, unknown>) => {
      const res = await request<ApiResponse<unknown>>(`/api/system/${prefix}/create`, { method: 'POST', data });
      if (res.code !== 0) throw new Error(res.message);
      return res.data;
    },
    update: async (id: string, data: Record<string, unknown>) => {
      const res = await request<ApiResponse<unknown>>(`/api/system/${prefix}/${id}`, { method: 'PUT', data });
      if (res.code !== 0) throw new Error(res.message);
      return res.data;
    },
    remove: async (id: string) => {
      await request(`/api/system/${prefix}/${id}`, { method: 'DELETE' });
    },
  };
}
