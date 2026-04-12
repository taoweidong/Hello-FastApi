interface MetaProps {
  /** 菜单显示标题 */
  title: string;
  /** 菜单图标 */
  icon: string;
  /** SVG图标名称（remix icon） */
  rSvgName: string;
  /** 是否在菜单中显示 */
  isShowMenu: boolean;
  /** 是否显示父级菜单 */
  isShowParent: boolean;
  /** 是否缓存页面(keep-alive) */
  isKeepalive: boolean;
  /** iframe内嵌链接 */
  frameUrl: string;
  /** iframe加载动画 */
  frameLoading: boolean;
  /** 进场动画名称 */
  transitionEnter: string;
  /** 离场动画名称 */
  transitionLeave: string;
  /** 禁止添加到标签页 */
  isHiddenTag: boolean;
  /** 固定标签页 */
  fixedTag: boolean;
  /** 动态路由层级 */
  dynamicLevel: number | null;
}

interface FormItemProps {
  /** 菜单类型（0-DIRECTORY目录、1-MENU页面、2-PERMISSION按钮/权限）*/
  menuType: number;
  higherMenuOptions: Record<string, unknown>[];
  parentId: number;
  name: string;
  path: string;
  component: string;
  rank: number;
  /** HTTP方法（PERMISSION类型使用） */
  method: string;
  /** 是否启用 */
  isActive: boolean;
  /** 菜单元数据 */
  meta: MetaProps;
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps, MetaProps };
