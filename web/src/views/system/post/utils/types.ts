interface FormItemProps {
  id?: string;
  postCode: string;
  postName: string;
  postSort: number;
  isActive: number;
  remark: string;
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
