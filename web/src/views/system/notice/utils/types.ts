interface FormItemProps {
  id?: string;
  title: string;
  content: string;
  noticeType: number;
  isActive: number;
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
