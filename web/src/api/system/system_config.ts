import { http } from "@/utils/http";
import { BaseApi, type PageParams, type ResultTable } from "../base";
import type { SystemConfig } from "../types";

class SystemConfigApi extends BaseApi<SystemConfig, SystemConfig> {
  constructor() {
    super("/config");
  }

  /** 获取配置列表（分页） — 与父类语义一致，显式声明返回分页结构 */
  list(params?: PageParams): Promise<ResultTable<SystemConfig>> {
    return http.request<ResultTable<SystemConfig>>("post", this.prefix, {
      data: params
    });
  }
}

export const systemConfigApi = new SystemConfigApi();
