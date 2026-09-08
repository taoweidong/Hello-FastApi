import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { IpRule } from "../types";

/** IP 规则创建/更新请求体 */
export type IpRulePayload = {
  ipAddress: string;
  ruleType?: string;
  reason?: string;
  isActive?: number;
  expiresAt?: string | null;
};

class IpRuleApi extends BaseApi<IpRule, IpRule, IpRulePayload> {
  constructor() {
    super("/ip-rule");
  }

  /** 批量删除 IP 规则 */
  override batchDelete(ids: Array<string>): Promise<Result> {
    return http.request<Result>("post", `${this.prefix}/batch-delete`, {
      data: { ids }
    });
  }

  /** 清空 IP 规则 */
  clear(): Promise<Result> {
    return http.request<Result>("post", `${this.prefix}/clear`);
  }
}

export const ipRuleApi = new IpRuleApi();
