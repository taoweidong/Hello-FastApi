/**
 * 系统管理 API - 兼容层
 *
 * 所有方法已迁移到 api/system/ 子模块，
 * 此文件保留为兼容层，重新导出全部方法。
 */
import { http } from "@/utils/http";
import { userApi } from "./system/user";
import { roleApi } from "./system/role";
import { menuApi } from "./system/menu";
import { deptApi } from "./system/dept";
import {
  getOnlineLogsList,
  forceOffline,
  getLoginLogsList,
  batchDeleteLoginLogs,
  clearLoginLogs,
  getOperationLogsList,
  batchDeleteOperationLogs,
  clearOperationLogs,
  getSystemLogsList,
  getSystemLogsDetail
} from "./system/log";
import { systemConfigApi } from "./system/system_config";
import { noticeApi } from "./system/notice";
import { postApi } from "./system/post";

// =============================================================================
// 类型导出（向后兼容）
// =============================================================================

type Result = {
  code: number;
  message: string;
  data?: Array<any>;
};

type ResultTable = {
  code: number;
  message: string;
  data?: {
    list: Array<any>;
    total?: number;
    pageSize?: number;
    currentPage?: number;
  };
};

// =============================================================================
// 用户管理 — 委托给 UserApi
// =============================================================================

/** 获取系统管理-用户管理列表 */
export const getUserList = (data?: object) => userApi.list(data);

/** 系统管理-用户管理-获取所有角色列表 */
export const getAllRoleList = () => userApi.getAllRoleList();

/** 系统管理-用户管理-根据userId，获取对应角色id列表 */
export const getRoleIds = (data?: object) => userApi.getRoleIds(data);

/** 创建用户 */
export const createUser = (data?: object) => userApi.create(data);

/** 更新用户 */
export const updateUser = (id: string, data?: object) =>
  userApi.partialUpdate(id, data);

/** 删除用户 */
export const deleteUser = (id: string) => userApi.destroy(id);

/** 批量删除用户 */
export const batchDeleteUser = (data?: object) =>
  userApi.batchDelete(data?.["ids"] ?? []);

/** 重置密码 */
export const resetPassword = (id: string, data?: object) =>
  userApi.resetPassword(id, data);

/** 修改用户状态 */
export const updateUserStatus = (id: string, data?: object) =>
  userApi.updateStatus(id, data);

/** 分配角色 */
export const assignUserRole = (data?: object) => userApi.assignUserRole(data);

// =============================================================================
// 角色管理 — 委托给 RoleApi
// =============================================================================

/** 获取系统管理-角色管理列表 */
export const getRoleList = (data?: object) => roleApi.list(data);

/** 创建角色 */
export const createRole = (data?: object) => roleApi.create(data);

/** 更新角色 */
export const updateRole = (id: string, data?: object) =>
  roleApi.partialUpdate(id, data);

/** 删除角色 */
export const deleteRole = (id: string) => roleApi.destroy(id);

/** 修改角色状态 */
export const updateRoleStatus = (id: string, data?: object) =>
  roleApi.updateStatus(id, data);

/** 获取角色管理-权限-菜单权限 */
export const getRoleMenu = (data?: object) => roleApi.getRoleMenu(data);

/** 获取角色管理-权限-菜单权限-根据角色id查对应菜单 */
export const getRoleMenuIds = (data?: object) => roleApi.getRoleMenuIds(data);

/** 保存角色菜单权限 */
export const saveRoleMenu = (roleId: string, menuIds: string[]) =>
  roleApi.saveRoleMenu(roleId, menuIds);

// =============================================================================
// 菜单管理 — 委托给 MenuApi
// =============================================================================

/** 获取系统管理-菜单管理列表 */
export const getMenuList = (data?: object) => menuApi.list(data);

/** 创建菜单 */
export const createMenu = (data?: object) => menuApi.create(data);

/** 更新菜单 */
export const updateMenu = (id: string, data?: object) =>
  menuApi.partialUpdate(id, data);

/** 删除菜单 */
export const deleteMenu = (id: string) => menuApi.destroy(id);

// =============================================================================
// 部门管理 — 委托给 DeptApi
// =============================================================================

/** 获取系统管理-部门管理列表 */
export const getDeptList = (data?: object) => deptApi.list(data);

/** 创建部门 */
export const createDept = (data?: object) => deptApi.create(data);

/** 更新部门 */
export const updateDept = (id: string, data?: object) =>
  deptApi.partialUpdate(id, data);

/** 删除部门 */
export const deleteDept = (id: string) => deptApi.destroy(id);

// =============================================================================
// 日志管理 — 直接从 log 模块导出
// =============================================================================

export {
  getOnlineLogsList,
  forceOffline,
  getLoginLogsList,
  batchDeleteLoginLogs,
  clearLoginLogs,
  getOperationLogsList,
  batchDeleteOperationLogs,
  clearOperationLogs,
  getSystemLogsList,
  getSystemLogsDetail
};

// =============================================================================
// IP 规则管理 — 暂保留内联
// =============================================================================

/** 获取 IP 规则列表 */
export const getIpRuleList = (data?: object) => {
  return http.request<ResultTable>("post", "/ip-rule", { data });
};

/** 创建 IP 规则 */
export const createIpRule = (data?: object) => {
  return http.request<Result>("post", "/ip-rule/create", { data });
};

/** 更新 IP 规则 */
export const updateIpRule = (id: string, data?: object) => {
  return http.request<Result>("put", `/ip-rule/${id}`, { data });
};

/** 删除 IP 规则 */
export const deleteIpRule = (id: string) => {
  return http.request<Result>("delete", `/ip-rule/${id}`);
};

/** 批量删除 IP 规则 */
export const batchDeleteIpRule = (data?: object) => {
  return http.request<Result>("post", "/ip-rule/batch-delete", { data });
};

/** 清空 IP 规则 */
export const clearIpRule = () => {
  return http.request<Result>("post", "/ip-rule/clear");
};

// =============================================================================
// 系统配置管理 — 委托给 SystemConfigApi
// =============================================================================

/** 获取系统配置列表 */
export const getConfigList = (data?: object) => systemConfigApi.list(data);

/** 创建系统配置 */
export const createConfig = (data?: object) => systemConfigApi.create(data);

/** 获取系统配置详情 */
export const getConfig = (id: string) => systemConfigApi.retrieve(id);

/** 更新系统配置 */
export const updateConfig = (id: string, data?: object) =>
  systemConfigApi.partialUpdate(id, data);

/** 删除系统配置 */
export const deleteConfig = (id: string) => systemConfigApi.destroy(id);

// =============================================================================
// 通知公告管理 — 委托给 NoticeApi
// =============================================================================

/** 获取通知公告列表 */
export const getNoticeList = (data?: object) => noticeApi.list(data);

/** 创建通知公告 */
export const createNotice = (data?: object) => noticeApi.create(data);

/** 获取通知公告详情 */
export const getNotice = (id: string) => noticeApi.retrieve(id);

/** 更新通知公告 */
export const updateNotice = (id: string, data?: object) =>
  noticeApi.partialUpdate(id, data);

/** 删除通知公告 */
export const deleteNotice = (id: string) => noticeApi.destroy(id);

/** 批量删除通知公告 */
export const batchDeleteNotice = (data?: object) =>
  noticeApi.batchDelete(data?.["ids"] ?? []);

/** 获取最新启用公告（顶栏铃铛） */
export const getLatestNotices = () => noticeApi.latest();

// =============================================================================
// 岗位管理 — 委托给 PostApi
// =============================================================================

/** 获取岗位列表 */
export const getPostList = (data?: object) => postApi.list(data);

/** 创建岗位 */
export const createPost = (data?: object) => postApi.create(data);

/** 获取岗位详情 */
export const getPost = (id: string) => postApi.retrieve(id);

/** 更新岗位 */
export const updatePost = (id: string, data?: object) =>
  postApi.partialUpdate(id, data);

/** 删除岗位 */
export const deletePost = (id: string) => postApi.destroy(id);

/** 批量删除岗位 */
export const batchDeletePost = (data?: object) =>
  postApi.batchDelete(data?.["ids"] ?? []);

/** 获取启用岗位下拉选项（用户表单岗位多选） */
export const getPostOptions = () => postApi.options();

/** 获取用户已分配的岗位 ID 列表 */
export const getUserPostIds = (userId: string) => postApi.userPosts(userId);
