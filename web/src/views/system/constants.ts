/**
 * 系统管理公共常量
 *
 * 菜单类型、请求方法、模式类型等枚举定义
 */

/** 菜单类型选项：DIRECTORY(目录) / MENU(页面) / PERMISSION(按钮/权限) */
export const MenuChoices = [
  { label: "目录", value: 0 },
  { label: "页面", value: 1 },
  { label: "权限", value: 2 }
] as const;

/** HTTP 方法选项（PERMISSION 类型使用） */
export const MethodChoices = [
  { label: "GET", value: "GET" },
  { label: "POST", value: "POST" },
  { label: "PUT", value: "PUT" },
  { label: "PATCH", value: "PATCH" },
  { label: "DELETE", value: "DELETE" }
] as const;

/** 模式类型选项 */
export const ModeChoices = [
  { label: "默认", value: 0 },
  { label: "强模式", value: 1 }
] as const;

/** 性别选项 */
export const GenderChoices = [
  { label: "男", value: 0 },
  { label: "女", value: 1 }
] as const;

/** IP 规则类型选项 */
export const IPRuleTypeChoices = [
  { label: "白名单", value: "whitelist" },
  { label: "黑名单", value: "blacklist" }
] as const;

/** 通用是否选项 */
export const YesNoChoices = [
  { label: "是", value: true },
  { label: "否", value: false }
] as const;

/** 字典状态选项 */
export const DictStatusChoices = [
  { label: "启用", value: 1 },
  { label: "停用", value: 0 }
] as const;

/** 根据菜单类型值获取标签 */
export function getMenuTypeLabel(type: number): string {
  return MenuChoices.find(c => c.value === type)?.label ?? "未知";
}

/** 根据菜单类型值获取 el-tag 类型 */
export function getMenuTagType(type: number): string {
  switch (type) {
    case 0:
      return "primary"; // 目录
    case 1:
      return "warning"; // 页面
    case 2:
      return "info"; // 权限
    default:
      return "";
  }
}
