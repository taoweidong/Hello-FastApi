import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemDictionary } from "../types";

class DictionaryApi extends BaseApi<SystemDictionary, SystemDictionary> {
  constructor() {
    super("/dictionary");
  }

  /** 获取字典列表（树结构，不分页，data 直接为数组） */
  listTree(
    params?: Record<string, unknown>
  ): Promise<Result<SystemDictionary[]>> {
    // params 缺省时补空对象：FastAPI body 参数必填，无 body 会 422
    return http.request<Result<SystemDictionary[]>>("post", this.prefix, {
      data: params ?? {}
    });
  }

  /** 根据字典名称查询字典项 */
  getByName(name: string): Promise<Result<SystemDictionary[]>> {
    return http.request<Result<SystemDictionary[]>>(
      "post",
      `${this.prefix}/getByName`,
      {
        data: { name }
      }
    );
  }

  /** 根据字典类型名称获取启用状态的字典项（公开取数接口，带后端缓存） */
  getByType<T = any>(name: string): Promise<Result<T>> {
    return http.request<Result<T>>("get", `${this.prefix}/type/${name}`);
  }
}

export const dictionaryApi = new DictionaryApi();
