/** Hello-FastApi 后端 API 服务层（全部域） */
import { request } from '@umijs/max';

export interface ApiRes<T = unknown> { code: number; message: string; data: T; }
export interface Page<T> { list: T[]; total: number; pageSize: number; currentPage: number; }

/** 请求选项（不含 getResponse，命中 umi request 直接返回 data 的重载） */
interface ReqOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  data?: unknown;
  params?: Record<string, unknown>;
  headers?: Record<string, string>;
}

async function req<T>(url: string, options: ReqOptions = {}): Promise<T> {
  const res = await request<ApiRes<T>>(url, options);
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

// ---- 认证 ----
export interface LoginResult {
  accessToken: string; refreshToken: string; expires: string;
  roles: string[]; permissions: string[];
  username: string; nickname: string; avatar: string;
}

export async function login(body: { username: string; password: string }): Promise<LoginResult> {
  const res = await request<ApiRes<LoginResult>>('/api/system/login', { method: 'POST', data: body });
  if (res.code !== 0) throw new Error(res.message);
  return res.data;
}

export async function logout(refreshToken: string): Promise<void> {
  try { await request('/api/system/logout', { method: 'POST', data: { refreshToken } }); } catch { /* 静默 */ }
}

export interface MineInfo { username: string; nickname: string; avatar: string; email: string; phone: string; }
export async function getMine(): Promise<MineInfo> { return req('/api/system/mine'); }

export interface MineLogRow { id: string; status: number; ipaddress: string; browser: string; createdTime: string | null; }
export async function getMineLogs(params: Record<string, unknown>): Promise<Page<MineLogRow>> { return req('/api/system/mine-logs', { params }); }

export interface AsyncRouteNode {
  path: string; name: string; rank?: number;
  meta?: { title?: string; icon?: string; showLink?: boolean; auths?: string[] };
  children?: AsyncRouteNode[];
}
export async function getAsyncRoutes(): Promise<AsyncRouteNode[]> { return req('/api/system/get-async-routes'); }

export async function updateProfile(data: Record<string, unknown>): Promise<unknown> {
  return req('/api/system/user/profile', { method: 'PUT', data });
}
export async function changePassword(data: { oldPassword: string; newPassword: string }): Promise<void> {
  await req('/api/system/user/change-password', { method: 'POST', data });
}
export async function resetUserPassword(id: string, newPassword: string): Promise<void> {
  await req(`/api/system/user/${id}/reset-password`, { method: 'PUT', data: { newPassword } });
}

// ---- 用户管理 ----
export interface UserRow {
  id: string; username: string; nickname: string | null;
  email: string | null; phone: string | null; isActive: number;
  roles: Array<{ id: string; name: string }>;
  dept: { id: string; name: string } | null;
  createdTime: string | null;
}

export async function getUsers(params: Record<string, unknown>): Promise<Page<UserRow>> { return req('/api/system/user', { method: 'POST', data: params }); }
export async function createUser(data: Record<string, unknown>): Promise<UserRow> { return req('/api/system/user/create', { method: 'POST', data }); }
export async function updateUser(id: string, data: Record<string, unknown>): Promise<UserRow> { return req(`/api/system/user/${id}`, { method: 'PUT', data }); }
export async function deleteUser(id: string): Promise<void> { await req(`/api/system/user/${id}`, { method: 'DELETE' }); }
export async function batchDeleteUsers(ids: string[]): Promise<number> { return req('/api/system/user/batch-delete', { method: 'POST', data: { ids } }); }
export async function updateUserStatus(id: string, isActive: number): Promise<void> { await req(`/api/system/user/${id}/status`, { method: 'PUT', data: { isActive } }); }
export async function assignRoles(userId: string, roleIds: string[]): Promise<void> { await req('/api/system/user/assign-role', { method: 'POST', data: { userId, roleIds } }); }

// ---- 角色管理 ----
export interface RoleRow { id: string; name: string; code: string; isActive: number; dataScope: number; description: string | null; createdTime: string | null; }
export interface RolePage extends Page<RoleRow> {}

export async function getRoles(params: Record<string, unknown>): Promise<RolePage> { return req('/api/system/role', { method: 'POST', data: params }); }
export async function createRole(data: Record<string, unknown>): Promise<RoleRow> { return req('/api/system/role/create', { method: 'POST', data }); }
export async function updateRole(id: string, data: Record<string, unknown>): Promise<RoleRow> { return req(`/api/system/role/${id}`, { method: 'PUT', data }); }
export async function updateRoleStatus(id: string, isActive: number): Promise<void> { await req(`/api/system/role/${id}/status`, { method: 'PUT', data: { isActive } }); }
export async function deleteRole(id: string): Promise<void> { await req(`/api/system/role/${id}`, { method: 'DELETE' }); }
export async function getRoleMenuIds(roleId: string): Promise<string[]> { return req('/api/system/role-menu-ids', { method: 'POST', data: { id: roleId } }); }
export async function saveRoleMenu(roleId: string, menuIds: string[]): Promise<void> { await req(`/api/system/role/${roleId}/menus`, { method: 'POST', data: { menuIds } }); }
export async function saveRoleDataScope(roleId: string, data: { dataScope: number; deptIds: string[] }): Promise<void> { await req(`/api/system/role/${roleId}/data-scope`, { method: 'POST', data }); }

// ---- 菜单管理 ----
export interface MenuRow {
  id: string; parentId: string | null; menuType: number; name: string;
  path: string; component: string | null; rank: number; isActive: number;
  method?: string | null;
  meta?: { title?: string; icon?: string; isShowMenu?: number; isKeepalive?: number; isHiddenTag?: number };
  children?: MenuRow[];
}
export async function getMenuList(): Promise<MenuRow[]> { return req('/api/system/menu', { method: 'POST' }); }
export interface MenuPayload { parentId?: string | null; menuType?: number; name: string; path?: string; component?: string; rank?: number; isActive?: number; title?: string; icon?: string; isShowMenu?: number; isKeepalive?: number; isHiddenTag?: number; method?: string; }
export async function createMenu(data: MenuPayload): Promise<MenuRow> { return req('/api/system/menu/create', { method: 'POST', data }); }
export async function updateMenu(id: string, data: MenuPayload): Promise<MenuRow> { return req(`/api/system/menu/${id}`, { method: 'PUT', data }); }
export async function updateMenuStatus(id: string, isActive: number): Promise<MenuRow> { return req(`/api/system/menu/${id}/status`, { method: 'PUT', data: { isActive } }); }
export async function deleteMenu(id: string): Promise<void> { await req(`/api/system/menu/${id}`, { method: 'DELETE' }); }

// ---- 部门管理 ----
export interface DeptRow { id: string; parentId: string | null; name: string; code: string; rank: number; isActive: number; description: string | null; children?: DeptRow[]; }
export async function getDeptList(): Promise<DeptRow[]> { return req('/api/system/dept', { method: 'POST' }); }
export interface DeptPayload { name: string; parentId?: string | null; code?: string; rank?: number; isActive?: number; description?: string; }
export async function createDept(data: DeptPayload): Promise<DeptRow> { return req('/api/system/dept/create', { method: 'POST', data }); }
export async function updateDept(id: string, data: DeptPayload): Promise<DeptRow> { return req(`/api/system/dept/${id}`, { method: 'PUT', data }); }
export async function deleteDept(id: string): Promise<void> { await req(`/api/system/dept/${id}`, { method: 'DELETE' }); }

// ---- 岗位管理 ----
export interface PostRow { id: string; postCode: string; postName: string; postSort: number; isActive: number; remark: string; createdTime: string | null; }
export interface PostPage extends Page<PostRow> {}
export async function getPosts(params: Record<string, unknown>): Promise<PostPage> { return req('/api/system/post', { method: 'POST', data: params }); }
export interface PostPayload { postCode: string; postName: string; postSort?: number; isActive?: number; remark?: string; }
export interface PostOption { id: string; postName: string; }
export async function createPost(data: PostPayload): Promise<PostRow> { return req('/api/system/post/create', { method: 'POST', data }); }
export async function updatePost(id: string, data: PostPayload): Promise<PostRow> { return req(`/api/system/post/${id}`, { method: 'PUT', data }); }
export async function deletePost(id: string): Promise<void> { await req(`/api/system/post/${id}`, { method: 'DELETE' }); }
export async function batchDeletePosts(ids: string[]): Promise<number> { return req('/api/system/post/batch-delete', { method: 'POST', data: { ids } }); }
export async function getPostOptions(): Promise<Array<{ id: string; postName: string }>> { return req('/api/system/post/options'); }

// ---- 字典管理 ----
export interface DictRow { id: string; parentId: string | null; name: string; label: string; value: string; sort: number; isActive: number; description: string | null; children?: DictRow[]; }
export async function getDictionaries(params?: Record<string, unknown>): Promise<DictRow[]> { return req('/api/system/dictionary', { method: 'POST', data: params }); }
export interface DictPayload { name: string; label?: string; value?: string; parentId?: string | null; sort?: number; isActive?: number; description?: string; }
export async function createDict(data: DictPayload): Promise<DictRow> { return req('/api/system/dictionary/create', { method: 'POST', data }); }
export async function updateDict(id: string, data: DictPayload): Promise<DictRow> { return req(`/api/system/dictionary/${id}`, { method: 'PUT', data }); }
export async function deleteDict(id: string): Promise<void> { await req(`/api/system/dictionary/${id}`, { method: 'DELETE' }); }
export async function getDictItemsByName(name: string): Promise<DictRow[]> { return req('/api/system/dictionary/getByName', { method: 'POST', data: { name } }); }

// ---- 参数配置 ----
export interface ConfigRow { id: string; key: string; value: string; isActive: number; description: string | null; createdTime: string | null; }
export interface ConfigPage extends Page<ConfigRow> {}
export async function getConfigs(params: Record<string, unknown>): Promise<ConfigPage> { return req('/api/system/config', { method: 'POST', data: params }); }
export interface ConfigPayload { key: string; value: string; isActive?: number; description?: string; }
export async function createConfig(data: ConfigPayload): Promise<ConfigRow> { return req('/api/system/config/create', { method: 'POST', data }); }
export async function updateConfig(id: string, data: Partial<ConfigPayload>): Promise<ConfigRow> { return req(`/api/system/config/${id}`, { method: 'PUT', data }); }
export async function deleteConfig(id: string): Promise<void> { await req(`/api/system/config/${id}`, { method: 'DELETE' }); }

// ---- IP 规则 ----
export interface IpRuleRow { id: string; ipAddress: string; ruleType: string; reason: string | null; isActive: number; createdTime: string | null; }
export interface IpRulePage extends Page<IpRuleRow> {}
export async function getIpRules(params: Record<string, unknown>): Promise<IpRulePage> { return req('/api/system/ip-rule', { method: 'POST', data: params }); }
export interface IpRulePayload { ipAddress: string; ruleType: string; reason?: string; isActive?: number; }
export async function createIpRule(data: IpRulePayload): Promise<IpRuleRow> { return req('/api/system/ip-rule/create', { method: 'POST', data }); }
export async function updateIpRule(id: string, data: Partial<IpRulePayload>): Promise<IpRuleRow> { return req(`/api/system/ip-rule/${id}`, { method: 'PUT', data }); }
export async function deleteIpRule(id: string): Promise<void> { await req(`/api/system/ip-rule/${id}`, { method: 'DELETE' }); }
export async function batchDeleteIpRules(ids: string[]): Promise<number> { return req('/api/system/ip-rule/batch-delete', { method: 'POST', data: { ids } }); }
export async function clearIpRules(): Promise<number> { return req('/api/system/ip-rule/clear'); }

// ---- 通知公告 ----
export interface NoticeRow { id: string; title: string; content: string; noticeType: number; isActive: number; publisherName: string; createdTime: string | null; }
export interface NoticePage extends Page<NoticeRow> {}
export async function getNotices(params: Record<string, unknown>): Promise<NoticePage> { return req('/api/system/notice', { method: 'POST', data: params }); }
export interface NoticePayload { title: string; content?: string; noticeType?: number; isActive?: number; }
export async function createNotice(data: NoticePayload): Promise<NoticeRow> { return req('/api/system/notice/create', { method: 'POST', data }); }
export async function updateNotice(id: string, data: NoticePayload): Promise<NoticeRow> { return req(`/api/system/notice/${id}`, { method: 'PUT', data }); }
export async function deleteNotice(id: string): Promise<void> { await req(`/api/system/notice/${id}`, { method: 'DELETE' }); }
export async function batchDeleteNotices(ids: string[]): Promise<number> { return req('/api/system/notice/batch-delete', { method: 'POST', data: { ids } }); }

// ---- 日志 ----
export interface LoginLogRow { id: string; status: number; ipaddress: string; browser: string; system: string; loginType: number; createdTime: string | null; }
export async function getLoginLogs(params: Record<string, unknown>): Promise<Page<LoginLogRow>> { return req('/api/system/login-logs', { method: 'POST', data: params }); }
export async function batchDeleteLoginLogs(ids: string[]): Promise<number> { return req('/api/system/login-logs/batch-delete', { method: 'POST', data: { ids } }); }
export async function clearLoginLogs(): Promise<number> { return req('/api/system/login-logs/clear'); }

export interface OperationLogRow { id: string; module: string; path: string; body: string; method: string; ipaddress: string; responseCode: number | null; statusCode: number | null; description: string; creatorId: string; createdTime: string | null; }
export async function getOperationLogs(params: Record<string, unknown>): Promise<Page<OperationLogRow>> { return req('/api/system/operation-logs', { method: 'POST', data: params }); }
export async function batchDeleteOperationLogs(ids: string[]): Promise<number> { return req('/api/system/operation-logs/batch-delete', { method: 'POST', data: { ids } }); }
export async function clearOperationLogs(): Promise<number> { return req('/api/system/operation-logs/clear'); }

// ---- 监控 ----
export interface ServerInfo { cpu: { coreCount: number; usedPercent: number }; memory: { total: string; used: string; free: string; usedPercent: number }; disk: { total: string; used: string; free: string; usedPercent: number }; system: { hostname: string; osName: string; osArch: string; pythonVersion: string; workDir: string; bootTime: string }; process: { pid: number; memoryUsed: string; cpuPercent: number; runningTime: string }; }
export async function getServerInfo(): Promise<ServerInfo> { return req('/api/system/server-info'); }

export interface CacheInfo { connected: boolean; message: string; version?: string; mode?: string; uptimeSeconds?: number; usedMemory?: string; usedMemoryPeak?: string; keyCount?: number; hitRate?: number; clients?: number; }
export async function getCacheInfo(): Promise<CacheInfo> { return req('/api/system/cache-info'); }
export interface CacheGroup { key: string; name: string; prefix: string; count: number; clearable: boolean; }
export async function getCacheGroups(): Promise<CacheGroup[]> { return req('/api/system/cache-groups'); }
export async function clearCacheGroup(group: string): Promise<number> { return req('/api/system/cache-clear', { method: 'POST', data: { group } }); }
export async function clearAllCache(): Promise<number> { return req('/api/system/cache-clear-all'); }

export interface OnlineRow { id: string; username: string; browser: string; system: string; loginTime: string; expiresAt: string; }
export async function getOnlineUsers(params: Record<string, unknown>): Promise<Page<OnlineRow>> { return req('/api/system/online-logs', { method: 'POST', data: params }); }
export async function forceOffline(id: string): Promise<void> { await req('/api/system/online-logs/force-offline', { method: 'POST', data: { id } }); }

export interface LogFile { name: string; sizeBytes: number; modifiedTime: string; }
export async function getLogFiles(): Promise<LogFile[]> { return req('/api/system/log-files'); }
export async function tailLogFile(name: string, lines?: number): Promise<string> { return req(`/api/system/log-files/${encodeURIComponent(name)}/tail`, { params: { lines: lines ?? 200 } }); }

// ---- 下拉数据 ----
export interface DeptTreeNode { id: string; name: string; children?: DeptTreeNode[]; }
export async function getDeptTree(): Promise<DeptTreeNode[]> { return req('/api/system/dept/tree'); }
export interface RoleOption { id: string; name: string; }
export async function getAllRoles(): Promise<RoleOption[]> { return req('/api/system/list-all-role'); }
export interface MenuTreeItem { id: string; parentId: string | null; name: string; menuType: number; title: string; }
export async function getMenuTree(): Promise<MenuTreeItem[]> { return req('/api/system/menu/tree'); }
