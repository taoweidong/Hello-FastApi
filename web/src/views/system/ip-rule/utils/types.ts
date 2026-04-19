interface FormItemProps {
  id?: string;
  ipAddress: string;
  ruleType: string;
  reason: string;
  isActive: number;
  expiresAt: string;
  description: string;
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
