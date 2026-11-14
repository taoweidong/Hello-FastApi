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
  /** 响应类型（下载等场景传 'blob'；与 axios ResponseType 一致以命中 umi request 重载） */
  responseType?: 'arraybuffer' | 'blob' | 'document' | 'json' | 'text';
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

export interface MineInfo { username: string; nickname: string; avatar: string; email: string; phone: string; description?: string; }
export async function getMine(): Promise<MineInfo> { return req('/api/system/mine'); }

/** 安全日志行（/mine-logs 返回 ip / loginTime 字段，与 /login-logs 的 ipaddress/createdTime 不同名） */
export interface MineLogRow { id: string; username: string; status: number; ip: string; browser: string; system: string; loginTime: string | null; }
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
  avatar: string | null; email: string | null; phone: string | null;
  gender: number | null; isActive: number;
  roles: Array<{ id: string; name: string }>;
  dept: { id: string; name: string } | null;
  createdTime: string | null; updatedTime: string | null;
  description: string | null;
}

export async function getUsers(params: Record<string, unknown>): Promise<Page<UserRow>> { return req('/api/system/user', { method: 'POST', data: params }); }
export async function createUser(data: Record<string, unknown>): Promise<UserRow> { return req('/api/system/user/create', { method: 'POST', data }); }
export async function updateUser(id: string, data: Record<string, unknown>): Promise<UserRow> { return req(`/api/system/user/${id}`, { method: 'PUT', data }); }
export async function deleteUser(id: string): Promise<void> { await req(`/api/system/user/${id}`, { method: 'DELETE' }); }
export async function batchDeleteUsers(ids: string[]): Promise<number> { return req('/api/system/user/batch-delete', { method: 'POST', data: { ids } }); }
export async function updateUserStatus(id: string, isActive: number): Promise<void> { await req(`/api/system/user/${id}/status`, { method: 'PUT', data: { isActive } }); }
export async function assignRoles(userId: string, roleIds: string[]): Promise<void> { await req('/api/system/user/assign-role', { method: 'POST', data: { userId, roleIds } }); }
/** 根据用户 ID 获取已分配角色 ID 列表（对齐 Vue userApi.getRoleIds） */
export async function getUserRoleIds(userId: string): Promise<string[]> { return req('/api/system/list-role-ids', { method: 'POST', data: { userId } }); }
/** 获取用户已分配的岗位 ID 列表（对齐 Vue postApi.userPosts） */
export async function getUserPosts(userId: string): Promise<string[]> { return req(`/api/system/post/user/${userId}`); }

// ---- 角色管理 ----
export interface RoleRow {
  id: string; name: string; code: string; isActive: number; dataScope: number;
  description: string | null; createdTime: string | null; updatedTime: string | null;
  /** 列表接口恒返回 []，详情接口才回填，仅用于数据权限回显 */
  deptIds?: string[];
}
export interface RolePage extends Page<RoleRow> {}

export async function getRoles(params: Record<string, unknown>): Promise<RolePage> { return req('/api/system/role', { method: 'POST', data: params }); }
/** 角色详情（列表接口不返回 deptIds，数据权限回填需调用详情） */
export async function getRoleDetail(id: string): Promise<RoleRow> { return req(`/api/system/role/${id}`); }
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
  createdTime?: string | null; updatedTime?: string | null;
  children?: MenuRow[];
}
export async function getMenuList(): Promise<MenuRow[]> { return req('/api/system/menu', { method: 'POST' }); }
export interface MenuPayload { parentId?: string | null; menuType?: number; name: string; path?: string; component?: string; rank?: number; isActive?: number; title?: string; icon?: string; isShowMenu?: number; isKeepalive?: number; isHiddenTag?: number; method?: string; }
export async function createMenu(data: MenuPayload): Promise<MenuRow> { return req('/api/system/menu/create', { method: 'POST', data }); }
export async function updateMenu(id: string, data: MenuPayload): Promise<MenuRow> { return req(`/api/system/menu/${id}`, { method: 'PUT', data }); }
export async function updateMenuStatus(id: string, isActive: number): Promise<MenuRow> { return req(`/api/system/menu/${id}/status`, { method: 'PUT', data: { isActive } }); }
export async function deleteMenu(id: string): Promise<void> { await req(`/api/system/menu/${id}`, { method: 'DELETE' }); }

// ---- 部门管理 ----
export interface DeptRow { id: string; parentId: string | null; name: string; code: string; rank: number; isActive: number; description: string | null; createdTime: string | null; updatedTime: string | null; children?: DeptRow[]; }
export async function getDeptList(): Promise<DeptRow[]> { return req('/api/system/dept', { method: 'POST' }); }
export interface DeptPayload { name: string; parentId?: string | null; code?: string; rank?: number; isActive?: number; description?: string | null; }
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
export interface DictRow { id: string; parentId: string | null; name: string; label: string; value: string; sort: number; isActive: number; description: string | null; createdTime: string | null; updatedTime: string | null; children?: DictRow[]; }
export async function getDictionaries(params?: Record<string, unknown>): Promise<DictRow[]> { return req('/api/system/dictionary', { method: 'POST', data: params }); }
export interface DictPayload { name: string; label?: string | null; value?: string | null; parentId?: string | null; sort?: number | null; isActive?: number; description?: string | null; }
export async function createDict(data: DictPayload): Promise<DictRow> { return req('/api/system/dictionary/create', { method: 'POST', data }); }
export async function updateDict(id: string, data: DictPayload): Promise<DictRow> { return req(`/api/system/dictionary/${id}`, { method: 'PUT', data }); }
export async function deleteDict(id: string): Promise<void> { await req(`/api/system/dictionary/${id}`, { method: 'DELETE' }); }
export async function getDictItemsByName(name: string): Promise<DictRow[]> { return req('/api/system/dictionary/getByName', { method: 'POST', data: { name } }); }
/** 按字典类型名称获取启用字典项（label/value 列表，对齐 Vue useDict 取数） */
export async function getDictByType(name: string): Promise<Array<{ label: string; value: string }>> { return req(`/api/system/dictionary/type/${encodeURIComponent(name)}`); }

// ---- 参数配置 ----
export interface ConfigRow { id: string; key: string; value: string; isActive: number; /** 访问级别 */ access?: number; /** 是否继承 */ inherit?: number; description: string | null; createdTime: string | null; updatedTime?: string | null; }
export interface ConfigPage extends Page<ConfigRow> {}
export async function getConfigs(params: Record<string, unknown>): Promise<ConfigPage> { return req('/api/system/config', { method: 'POST', data: params }); }
export interface ConfigPayload { key: string; value: string; isActive?: number; /** 访问级别（0-999） */ access?: number; /** 是否继承（0/1） */ inherit?: number; description?: string; }
export async function createConfig(data: ConfigPayload): Promise<ConfigRow> { return req('/api/system/config/create', { method: 'POST', data }); }
export async function updateConfig(id: string, data: Partial<ConfigPayload>): Promise<ConfigRow> { return req(`/api/system/config/${id}`, { method: 'PUT', data }); }
export async function deleteConfig(id: string): Promise<void> { await req(`/api/system/config/${id}`, { method: 'DELETE' }); }

// ---- IP 规则 ----
export interface IpRuleRow { id: string; ipAddress: string; ruleType: string; reason: string | null; isActive: number; expiresAt: string | null; description: string | null; createdTime: string | null; updatedTime: string | null; }
export interface IpRulePage extends Page<IpRuleRow> {}
export async function getIpRules(params: Record<string, unknown>): Promise<IpRulePage> { return req('/api/system/ip-rule', { method: 'POST', data: params }); }
export interface IpRulePayload { ipAddress: string; ruleType: string; reason?: string | null; isActive?: number; expiresAt?: string | null; description?: string | null; }
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
/** 公告详情（对齐 Vue noticeApi.retrieve，点击标题查看只读弹窗） */
export async function getNotice(id: string): Promise<NoticeRow> { return req(`/api/system/notice/${id}`); }
/** 顶栏通知铃铛：最新启用公告/通知（公告 noticeType=2 → tab1，通知 noticeType=1 → tab2） */
export async function getLatestNotices(): Promise<NoticeRow[]> { return req('/api/system/notice/latest'); }

// ---- 令牌刷新 / 头像 / 日志下载 ----
export interface RefreshTokenResult { accessToken: string; refreshToken: string; expires: string; }
/** 刷新令牌（旧 refreshToken 单次使用后拉黑，返回新令牌对） */
export async function refreshTokenApi(refreshToken: string): Promise<RefreshTokenResult> { return req('/api/system/refresh-token', { method: 'POST', data: { refreshToken } }); }
/** 上传头像（FormData，覆写 JSON 头为 multipart） */
export async function uploadAvatar(data: FormData): Promise<{ avatar: string }> { return req('/api/system/user/avatar', { method: 'POST', data, headers: { 'Content-Type': 'multipart/form-data' } }); }
/** 下载日志文件（FileResponse 直返 Blob，不走 ApiRes 解包） */
export async function downloadLogFile(name: string): Promise<Blob> {
  return await request<Blob>(`/api/system/log-files/${encodeURIComponent(name)}`, { params: { download: true }, responseType: 'blob' });
}

// ---- 日志 ----
export interface LoginLogRow { id: string; status: number; ipaddress: string; browser: string; system: string; /** User-Agent */ agent?: string; loginType: number; creatorId?: string; createdTime: string | null; }
export async function getLoginLogs(params: Record<string, unknown>): Promise<Page<LoginLogRow>> { return req('/api/system/login-logs', { method: 'POST', data: params }); }
export async function batchDeleteLoginLogs(ids: string[]): Promise<number> { return req('/api/system/login-logs/batch-delete', { method: 'POST', data: { ids } }); }
export async function clearLoginLogs(): Promise<number> { return req('/api/system/login-logs/clear'); }

export interface OperationLogRow { id: string; module: string; path: string; body: string; method: string; ipaddress: string; browser?: string; system?: string; responseCode: number | null; responseResult?: string; statusCode: number | null; description: string; creatorId: string; createdTime: string | null; }
export async function getOperationLogs(params: Record<string, unknown>): Promise<Page<OperationLogRow>> { return req('/api/system/operation-logs', { method: 'POST', data: params }); }
export async function batchDeleteOperationLogs(ids: string[]): Promise<number> { return req('/api/system/operation-logs/batch-delete', { method: 'POST', data: { ids } }); }
export async function clearOperationLogs(): Promise<number> { return req('/api/system/operation-logs/clear'); }

// ---- 监控 ----
export interface ServerInfo { cpu: { coreCount: number; usedPercent: number }; memory: { total: string; used: string; free: string; usedPercent: number }; disk: { total: string; used: string; free: string; usedPercent: number }; system: { hostname: string; osName: string; osArch: string; pythonVersion: string; workDir: string; bootTime: string }; process: { pid: number; memoryUsed: string; cpuPercent: number; runningTime: string }; }
export async function getServerInfo(): Promise<ServerInfo> { return req('/api/system/server-info'); }

/** 缓存监控命令统计条目（命令调用统计 Top10） */
export interface CacheCommandStat { name: string; calls: number; usec: number; }
export interface CacheInfo { connected: boolean; message: string; version?: string; mode?: string; uptimeSeconds?: number; usedMemory?: string; usedMemoryPeak?: string; keyCount?: number; hitRate?: number; clients?: number; commandStats?: CacheCommandStat[]; }
export async function getCacheInfo(): Promise<CacheInfo> { return req('/api/system/cache-info'); }
export interface CacheGroup { key: string; name: string; prefix: string; count: number; clearable: boolean; }
export async function getCacheGroups(): Promise<CacheGroup[]> { return req('/api/system/cache-groups'); }
export async function clearCacheGroup(group: string): Promise<number> { return req('/api/system/cache-clear', { method: 'POST', data: { group } }); }
export async function clearAllCache(): Promise<number> { return req('/api/system/cache-clear-all'); }

export interface OnlineRow { id: string; username: string; /** 登录 IP */ ip?: string | null; browser: string; system: string; loginTime: string; expiresAt: string; }
export async function getOnlineUsers(params: Record<string, unknown>): Promise<Page<OnlineRow>> { return req('/api/system/online-logs', { method: 'POST', data: params }); }
export async function forceOffline(id: string): Promise<void> { await req('/api/system/online-logs/force-offline', { method: 'POST', data: { id } }); }

export interface LogFile { name: string; sizeBytes: number; modifiedTime: string; }
export async function getLogFiles(): Promise<LogFile[]> { return req('/api/system/log-files'); }
/** 日志尾部内容（对齐 Vue LogTail：{ name, lines, content }） */
export interface LogTail { name: string; lines: number; content: string; }
export async function tailLogFile(name: string, lines?: number): Promise<LogTail> { return req(`/api/system/log-files/${encodeURIComponent(name)}/tail`, { params: { lines: lines ?? 200 } }); }

// ---- 下拉数据 ----
export interface DeptTreeNode { id: string; name: string; children?: DeptTreeNode[]; }
export async function getDeptTree(): Promise<DeptTreeNode[]> { return req('/api/system/dept/tree'); }
export interface RoleOption { id: string; name: string; }
export async function getAllRoles(): Promise<RoleOption[]> { return req('/api/system/list-all-role'); }
export interface MenuTreeItem { id: string; parentId: string | null; name: string; menuType: number; title: string; }
export async function getMenuTree(): Promise<MenuTreeItem[]> { return req('/api/system/menu/tree'); }

// ---- 示例数据（Univer 表格 CRUD 示例） ----
export interface ExampleData {
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
}

export type ExampleDataCreatePayload = Omit<ExampleData, 'id' | 'creatorId' | 'createdTime' | 'updatedTime'>;
export type ExampleDataUpdatePayload = Omit<ExampleData, 'creatorId' | 'createdTime' | 'updatedTime'>;

/** Univer 差异回写载荷 */
export interface ExampleBatchSavePayload {
  creates: Array<Omit<ExampleDataCreatePayload, 'isActive'> & { isActive?: number }>;
  updates: ExampleDataUpdatePayload[];
  deletes: string[];
}

export interface ExampleBatchSaveResult { created: number; updated: number; deleted: number; }

/** 分页列表（Univer 页面以大 pageSize 拉全量；pageSize 上限 100） */
export async function getExampleRows(data?: { pageNum?: number; pageSize?: number; name?: string; category?: string; isActive?: number }): Promise<Page<ExampleData>> {
  return req('/api/system/example-data', { method: 'POST', data });
}

/** 按 ID 获取 */
export async function getExampleRow(id: string): Promise<ExampleData> { return req(`/api/system/example-data/${id}`); }

/** 创建单行 */
export async function createExampleRow(data: ExampleDataCreatePayload): Promise<ExampleData> { return req('/api/system/example-data/create', { method: 'POST', data }); }

/** 更新单行（全行回写） */
export async function updateExampleRow(id: string, data: ExampleDataUpdatePayload): Promise<ExampleData> { return req(`/api/system/example-data/${id}`, { method: 'PUT', data }); }

/** 删除单行 */
export async function deleteExampleRow(id: string): Promise<void> { await req(`/api/system/example-data/${id}`, { method: 'DELETE' }); }

/** 批量删除 */
export async function batchDeleteExampleRows(ids: string[]): Promise<{ deleted: number }> { return req('/api/system/example-data/batch-delete', { method: 'POST', data: ids }); }

/** 批量保存（Univer 差异回写：creates + updates + deletes 单事务） */
export async function batchSaveExampleRows(data: ExampleBatchSavePayload): Promise<ExampleBatchSaveResult> { return req('/api/system/example-data/batch-save', { method: 'POST', data }); }
