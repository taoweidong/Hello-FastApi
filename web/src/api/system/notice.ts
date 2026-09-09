import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";
import type { SystemNotice } from "../types";

class NoticeApi extends BaseApi<SystemNotice, SystemNotice> {
  constructor() {
    super("/notice");
  }

  /** 获取最新启用公告（仅需登录，供顶栏通知铃铛展示） */
  latest<T = any>(): Promise<Result<Array<T>>> {
    return http.request<Result<Array<T>>>("get", `${this.prefix}/latest`);
  }
}

export const noticeApi = new NoticeApi();
