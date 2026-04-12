import { http } from "@/utils/http";
import { BaseApi, type Result, type ResultTable } from "../base";

class UserApi extends BaseApi {
  constructor() {
    super("/user");
  }

  /** 获取所有角色列表 */
  getAllRoleList(): Promise<Result> {
    return http.request<Result>("get", "/list-all-role");
  }

  /** 根据userId获取对应角色id列表 */
  getRoleIds(data?: object): Promise<Result> {
    return http.request<Result>("post", "/list-role-ids", { data });
  }

  /** 重置密码 */
  resetPassword(id: string, data?: object): Promise<Result> {
    return http.request<Result>("put", `${this.prefix}/${id}/reset-password`, {
      data
    });
  }

  /** 分配角色 */
  assignUserRole(data?: object): Promise<Result> {
    return http.request<Result>("post", "/user/assign-role", { data });
  }
}

export const userApi = new UserApi();
