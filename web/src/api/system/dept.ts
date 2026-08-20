import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";

class DeptApi extends BaseApi {
  constructor() {
    super("/dept");
  }

  /** 获取部门列表（树结构，不分页） */
  list<T = any>(params?: object): Promise<Result<T>> {
    return http.request<Result<T>>("post", this.prefix, { data: params });
  }

  /** 获取部门树结构（全量，数据权限配置用） */
  tree<T = any>(): Promise<Result<T>> {
    return http.request<Result<T>>("get", `${this.prefix}/tree`);
  }
}

export const deptApi = new DeptApi();
