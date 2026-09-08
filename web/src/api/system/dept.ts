import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemDept } from "../types";

class DeptApi extends BaseApi<SystemDept, SystemDept> {
  constructor() {
    super("/dept");
  }

  /** 获取部门列表（树结构，不分页，data 直接为数组） */
  listTree(params?: Record<string, unknown>): Promise<Result<SystemDept[]>> {
    // params 缺省时补空对象：FastAPI body 参数必填，无 body 会 422
    return http.request<Result<SystemDept[]>>("post", this.prefix, {
      data: params ?? {}
    });
  }

  /** 获取部门树结构（全量，数据权限配置用） */
  tree(): Promise<Result<SystemDept[]>> {
    return http.request<Result<SystemDept[]>>("get", `${this.prefix}/tree`);
  }
}

export const deptApi = new DeptApi();
