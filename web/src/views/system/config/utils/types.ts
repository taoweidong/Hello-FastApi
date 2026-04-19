interface FormItemProps {
  id?: string;
  key: string;
  value: string;
  access: number;
  isActive: number;
  inherit: number;
  description: string;
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
