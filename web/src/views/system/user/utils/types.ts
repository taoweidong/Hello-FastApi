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
}

interface RoleFormItemProps {
  username: string;
  nickname: string;
  /** 角色列表 */
  roleOptions: any[];
  /** 选中的角色列表 */
  ids: Record<number, unknown>[];
}
interface RoleFormProps {
  formInline: RoleFormItemProps;
}

export type { FormItemProps, FormProps, RoleFormItemProps, RoleFormProps };
