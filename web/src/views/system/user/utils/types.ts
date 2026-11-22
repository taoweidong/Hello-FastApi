import type { PostOption } from "@/api/system/post";

interface FormItemProps {
  id?: number;
  /** 用于判断是`新增`还是`修改` */
  title: string;
  higherDeptOptions: Record<string, unknown>[];
  parentId: number;
  nickname: string;
  username: string;
  password: string;
  phone: string | number;
  email: string;
  gender: string | number;
  isActive: number;
  /** 岗位下拉选项（启用岗位） */
  postOptions: PostOption[];
  /** 已选岗位 ID 列表 */
  postIds: string[];
  dept?: {
    id?: number;
    name?: string;
  };
  description: string;
}
interface FormProps {
  formInline: FormItemProps;
  /** 表单区加载态：编辑时异步回填已分配岗位期间遮罩表单 */
  formLoading?: boolean;
}

import type { SystemRole } from "@/api/types";

interface RoleFormItemProps {
  username: string;
  nickname: string;
  /** 角色下拉选项列表 */
  roleOptions: SystemRole[];
  /**
   * 选中的角色 ID 列表
   *
   * 来源为 `getRoleIds` 返回的 `string[]`，并直接作为 `assignUserRole` 的
   * `roleIds` 提交给后端（后端 AssignRoleDTO.roleIds 为 list[str]）。
   */
  ids: string[];
}
interface RoleFormProps {
  formInline: RoleFormItemProps;
  /** 表单区加载态：异步回填已分配角色期间遮罩表单 */
  formLoading?: boolean;
}

export type { FormItemProps, FormProps, RoleFormItemProps, RoleFormProps };
