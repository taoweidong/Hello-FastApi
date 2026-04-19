import { http } from "@/utils/http";
import { BaseApi, type ResultTable } from "../base";

class SystemConfigApi extends BaseApi {
  constructor() {
    super("/config");
  }

  /** 获取配置列表（分页） — 覆写父类list，使用ResultTable */
  list<T = any>(params?: object): Promise<ResultTable<T>> {
    return http.request<ResultTable<T>>("post", this.prefix, { data: params });
  }
}

export const systemConfigApi = new SystemConfigApi();
