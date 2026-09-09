interface FormItemProps {
  id?: string;
  higherDeptOptions: Record<string, unknown>[];
  parentId: number;
  name: string;
  code?: string;
  principal: string;
  phone: string | number;
  email: string;
  rank: number;
  isActive: number;
  description: string;
  /** 权限模式(0-OR, 1-AND)：后端 DepartmentCreateDTO 必填，表单无此输入项，提交时默认 0 */
  modeType?: number;
  /** 是否自动绑定角色：后端 DepartmentCreateDTO 必填，表单无此输入项，提交时默认 0 */
  autoBind?: number;
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
