import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemMenu } from "../types";

class MenuApi extends BaseApi<SystemMenu, SystemMenu> {
  constructor() {
    super("/menu");
  }

  /** 获取菜单列表（树结构，不分页，data 直接为数组） */
  listTree(params?: Record<string, unknown>): Promise<Result<SystemMenu[]>> {
    // params 缺省时补空对象：FastAPI body 参数必填，无 body 会 422
    return http.request<Result<SystemMenu[]>>("post", this.prefix, {
      data: params ?? {}
    });
  }
}

export const menuApi = new MenuApi();
