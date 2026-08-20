// 虽然字段很少 但是抽离出来 后续有扩展字段需求就很方便了

interface FormItemProps {
  /** 角色名称 */
  name: string;
  /** 角色编号 */
  code: string;
  /** 是否启用 */
  isActive: number;
  /** 数据权限范围：1全部/2自定义/3本部门/4本部门及以下/5仅本人 */
  dataScope: number;
  /** 描述 */
  description: string;
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
