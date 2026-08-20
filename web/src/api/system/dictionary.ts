import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";

class DictionaryApi extends BaseApi {
  constructor() {
    super("/dictionary");
  }

  /** 获取字典列表（树结构，不分页） */
  list<T = any>(params?: object): Promise<Result<T>> {
    return http.request<Result<T>>("post", this.prefix, { data: params });
  }

  /** 根据字典名称查询字典项 */
  getByName<T = any>(name: string): Promise<Result<T>> {
    return http.request<Result<T>>("post", `${this.prefix}/getByName`, {
      data: { name }
    });
  }

  /** 根据字典类型名称获取启用状态的字典项（公开取数接口，带后端缓存） */
  getByType<T = any>(name: string): Promise<Result<T>> {
    return http.request<Result<T>>("get", `${this.prefix}/type/${name}`);
  }
}

export const dictionaryApi = new DictionaryApi();
