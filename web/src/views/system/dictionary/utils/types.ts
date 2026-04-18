interface FormItemProps {
  id?: string;
  higherDictOptions: Record<string, unknown>[];
  parentId: string | number;
  name: string;
  label: string;
  value: string;
  sort: number | null;
  isActive: number;
  description: string;
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
