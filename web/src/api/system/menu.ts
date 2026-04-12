import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";

class MenuApi extends BaseApi {
  constructor() {
    super("/menu");
  }

  /** 获取菜单列表（树结构，不分页） */
  list<T = any>(params?: object): Promise<Result<T>> {
    return http.request<Result<T>>("post", this.prefix, { data: params });
  }
}

export const menuApi = new MenuApi();
