import { http, request } from "./client";

/** 用户行（与后端 UserResponseDTO 对齐，camelCase） */
export interface UserRow {
  id: string;
  username: string;
  nickname: string | null;
  email: string | null;
  phone: string | null;
  gender: number;
  avatar: string | null;
  isActive: number;
  isStaff: number;
  modeType: number;
  roles: Array<{ id: string; name: string }>;
  dept: { id: string; name: string } | null;
  description: string | null;
  createdTime: string | null;
  updatedTime: string | null;
}

export interface UserListParams {
  pageNum?: number;
  pageSize?: number;
  username?: string;
  phone?: string;
  email?: string;
  isActive?: number;
  deptId?: string;
}

export interface UserPage {
  list: UserRow[];
  total: number;
  pageSize: number;
  currentPage: number;
}

/** 分页列表 */
export async function getUsers(params: UserListParams): Promise<UserPage> {
  return request<UserPage>({ method: "post", url: "/user", data: params });
}

export interface UserCreatePayload {
  username: string;
  password: string;
  nickname?: string;
  email?: string;
  phone?: string;
  deptId?: string;
  postIds?: string[];
  isActive?: number;
}

export async function createUser(data: UserCreatePayload): Promise<UserRow> {
  return request<UserRow>({ method: "post", url: "/user/create", data });
}

export interface UserUpdatePayload {
  nickname?: string;
  email?: string;
  phone?: string;
  isActive?: number;
  deptId?: string;
  postIds?: string[];
  description?: string;
}

export async function updateUser(id: string, data: UserUpdatePayload): Promise<UserRow> {
  return request<UserRow>({ method: "put", url: `/user/${id}`, data });
}

export async function deleteUser(id: string): Promise<void> {
  await http.delete(`/user/${id}`);
}

export async function batchDeleteUsers(ids: string[]): Promise<number> {
  const data = await request<{ deleted: number }>({
    method: "post",
    url: "/user/batch-delete",
    data: ids
  });
  return data.deleted;
}

export async function updateUserStatus(id: string, isActive: number): Promise<void> {
  await http.put(`/user/${id}/status`, { isActive });
}

export async function assignRoles(userId: string, roleIds: string[]): Promise<void> {
  await http.post("/user/assign-role", { userId, roleIds });
}

export async function resetPassword(id: string, newPassword: string): Promise<void> {
  await http.put(`/user/${id}/reset-password`, { newPassword });
}

/** 部门节点（/dept/tree） */
export interface DeptNode {
  id: string;
  name: string;
  parentId: string | number | null;
  children?: DeptNode[];
}

export async function getDeptTree(): Promise<DeptNode[]> {
  return request<DeptNode[]>({ method: "get", url: "/dept/tree" });
}

/** 角色简单列表（/list-all-role） */
export interface RoleOption {
  id: string;
  name: string;
}

export async function getAllRoles(): Promise<RoleOption[]> {
  return request<RoleOption[]>({ method: "get", url: "/list-all-role" });
}

/** 岗位选项（/post/options） */
export interface PostOption {
  id: string;
  postName: string;
}

export async function getPostOptions(): Promise<PostOption[]> {
  return request<PostOption[]>({ method: "get", url: "/post/options" });
}
