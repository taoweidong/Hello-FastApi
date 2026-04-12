interface FormItemProps {
  higherDeptOptions: Record<string, unknown>[];
  parentId: number;
  name: string;
  principal: string;
  phone: string | number;
  email: string;
  rank: number;
  isActive: boolean;
  description: string;
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
