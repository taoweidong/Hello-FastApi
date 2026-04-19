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
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
