import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";

/** 岗位下拉选项结构 */
export type PostOption = {
  id: string;
  postCode: string;
  postName: string;
  postSort: number;
};

class PostApi extends BaseApi {
  constructor() {
    super("/post");
  }

  /** 获取启用岗位下拉选项（仅需登录，供用户表单选择） */
  options(): Promise<Result<Array<PostOption>>> {
    return http.request<Result<Array<PostOption>>>(
      "get",
      `${this.prefix}/options`
    );
  }

  /** 获取用户已分配的岗位 ID 列表 */
  userPosts(userId: string): Promise<Result<Array<string>>> {
    return http.request<Result<Array<string>>>(
      "get",
      `${this.prefix}/user/${userId}`
    );
  }
}

export const postApi = new PostApi();
