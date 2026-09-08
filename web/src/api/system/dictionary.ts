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
    return http.request<Result<SystemDictionary[]>>("post", this.prefix, {
      data: params
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
}

export const dictionaryApi = new DictionaryApi();
