import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemRole, SystemUser } from "../types";

class UserApi extends BaseApi<SystemUser, SystemUser> {
  constructor() {
    super("/user");
  }

  /** 获取所有角色列表 */
  getAllRoleList(): Promise<Result<SystemRole[]>> {
    return http.request<Result<SystemRole[]>>("get", "/list-all-role");
  }

  /** 根据userId获取对应角色id列表 */
  getRoleIds(data?: { userId?: string }): Promise<Result<string[]>> {
    return http.request<Result<string[]>>("post", "/list-role-ids", { data });
  }

  /** 重置密码 */
  resetPassword(
    id: string,
    data: { newPassword: string }
  ): Promise<Result<void>> {
    return http.request<Result<void>>(
      "put",
      `${this.prefix}/${id}/reset-password`,
      {
        data
      }
    );
  }

  /** 分配角色 */
  assignUserRole(data: {
    userId: string;
    roleIds: string[];
  }): Promise<Result<void>> {
    return http.request<Result<void>>("post", "/user/assign-role", { data });
  }
}

export const userApi = new UserApi();
