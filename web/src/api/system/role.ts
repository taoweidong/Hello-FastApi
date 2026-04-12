import { http } from "@/utils/http";
import { BaseApi, type Result, type ResultTable } from "../base";

class RoleApi extends BaseApi {
  constructor() {
    super("/role");
  }

  /** 获取角色管理-权限-菜单权限（树结构） */
  getRoleMenu(data?: object): Promise<Result> {
    return http.request<Result>("post", "/role-menu", { data });
  }

  /** 根据角色id查对应菜单id列表 */
  getRoleMenuIds(data?: object): Promise<Result> {
    return http.request<Result>("post", "/role-menu-ids", { data });
  }

  /** 保存角色菜单权限 */
  saveRoleMenu(roleId: string, menuIds: string[]): Promise<Result> {
    return http.request<Result>("post", `/role/${roleId}/menu`, {
      data: { menuIds }
    });
  }
}

export const roleApi = new RoleApi();
