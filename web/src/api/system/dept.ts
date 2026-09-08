import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemDept } from "../types";

class DeptApi extends BaseApi<SystemDept, SystemDept> {
  constructor() {
    super("/dept");
  }

  /** 获取部门列表（树结构，不分页，data 直接为数组） */
  listTree(params?: Record<string, unknown>): Promise<Result<SystemDept[]>> {
    return http.request<Result<SystemDept[]>>("post", this.prefix, {
      data: params
    });
  }
}

export const deptApi = new DeptApi();
