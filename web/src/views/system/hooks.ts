// 抽离可公用的工具函数等用于系统管理页面逻辑
import { computed } from "vue";

export function usePublicHooks() {
  const switchStyle = computed(() => {
    return {
      "--el-switch-on-color": "#6abe39",
      "--el-switch-off-color": "#e84749"
    };
  });

  return {
    /** 表现更鲜明的`el-switch`组件  */
    switchStyle
  };
}

/**
 * 格式化上级部门选项（用于级联选择器）
 * 根据 isActive 字段追加 disabled 属性
 */
export function formatHigherDeptOptions(
  treeList: Array<Record<string, any>>
): Array<Record<string, any>> {
  if (!treeList || !treeList.length) return [];
  const newTreeList = [];
  for (let i = 0; i < treeList.length; i++) {
    treeList[i].disabled = !treeList[i].isActive;
    if (treeList[i].children) {
      formatHigherDeptOptions(treeList[i].children);
    }
    newTreeList.push(treeList[i]);
  }
  return newTreeList;
}

/**
 * 格式化上级菜单选项（用于级联选择器）
 * 用 meta.title 或 name 作为显示标题
 */
export function formatHigherMenuOptions(
  treeList: Array<Record<string, any>>
): Array<Record<string, any>> {
  if (!treeList || !treeList.length) return [];
  const newTreeList = [];
  for (let i = 0; i < treeList.length; i++) {
    treeList[i].title = treeList[i].meta?.title ?? treeList[i].name;
    if (treeList[i].children) {
      formatHigherMenuOptions(treeList[i].children);
    }
    newTreeList.push(treeList[i]);
  }
  return newTreeList;
}

/**
 * 获取菜单类型标签
 * 0-DIRECTORY(目录) 1-MENU(页面) 2-PERMISSION(按钮/权限)
 */
export function getMenuType(
  type: number,
  text = false
): "primary" | "warning" | "info" | "" | string {
  switch (type) {
    case 0:
      return text ? "目录" : "primary";
    case 1:
      return text ? "页面" : "warning";
    case 2:
      return text ? "权限" : "info";
    default:
      return text ? "未知" : "";
  }
}

/**
 * 自定义角色权限选项（用于菜单权限树）
 * 将扁平菜单列表转换为树形选择器可用格式
 */
export function customRolePermissionOptions(
  menus: Array<Record<string, any>>
): Array<Record<string, any>> {
  return menus.map(menu => ({
    id: menu.id,
    title: menu.meta?.title ?? menu.name,
    children: menu.children
      ? customRolePermissionOptions(menu.children)
      : undefined
  }));
}
