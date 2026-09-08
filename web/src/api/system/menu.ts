import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemMenu } from "../types";

class MenuApi extends BaseApi<SystemMenu, SystemMenu> {
  constructor() {
    super("/menu");
  }

  /** 获取菜单列表（树结构，不分页，data 直接为数组） */
  listTree(params?: Record<string, unknown>): Promise<Result<SystemMenu[]>> {
    return http.request<Result<SystemMenu[]>>("post", this.prefix, {
      data: params
    });
  }
}

export const menuApi = new MenuApi();
