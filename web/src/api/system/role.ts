import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemMenu, SystemRole } from "../types";

class RoleApi extends BaseApi<SystemRole, SystemRole> {
  constructor() {
    super("/role");
  }

  /**
   * 获取角色管理-权限-菜单权限（树结构）
   *
   * 后端 `/role-menu` 不接受请求体（仅依赖当前登录用户），故无参数。
   */
  getRoleMenu(): Promise<Result<SystemMenu[]>> {
    return http.request<Result<SystemMenu[]>>("post", "/role-menu");
  }

  /** 根据角色id查对应菜单id列表 */
  getRoleMenuIds(data: { id: string }): Promise<Result<string[]>> {
    return http.request<Result<string[]>>("post", "/role-menu-ids", { data });
  }

  /** 保存角色菜单权限 */
  saveRoleMenu(roleId: string, menuIds: string[]): Promise<Result<void>> {
    return http.request<Result<void>>("post", `/role/${roleId}/menus`, {
      data: { menuIds }
    });
  }
}

export const roleApi = new RoleApi();
