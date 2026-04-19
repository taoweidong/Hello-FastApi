import type { OptionsType } from "@/components/ReSegmented";

/** 菜单类型：0-DIRECTORY(目录) 1-MENU(页面) */
const menuTypeOptions: Array<OptionsType> = [
  {
    label: "目录",
    value: 0
  },
  {
    label: "页面",
    value: 1
  }
];

const showLinkOptions: Array<OptionsType> = [
  {
    label: "显示",
    tip: "会在菜单中显示",
    value: true
  },
  {
    label: "隐藏",
    tip: "不会在菜单中显示",
    value: false
  }
];

const fixedTagOptions: Array<OptionsType> = [
  {
    label: "固定",
    tip: "当前菜单名称固定显示在标签页且不可关闭",
    value: true
  },
  {
    label: "不固定",
    tip: "当前菜单名称不固定显示在标签页且可关闭",
    value: false
  }
];

const keepAliveOptions: Array<OptionsType> = [
  {
    label: "缓存",
    tip: "会保存该页面的整体状态，刷新后会清空状态",
    value: true
  },
  {
    label: "不缓存",
    tip: "不会保存该页面的整体状态",
    value: false
  }
];

const hiddenTagOptions: Array<OptionsType> = [
  {
    label: "允许",
    tip: "当前菜单名称或自定义信息允许添加到标签页",
    value: false
  },
  {
    label: "禁止",
    tip: "当前菜单名称或自定义信息禁止添加到标签页",
    value: true
  }
];

const showParentOptions: Array<OptionsType> = [
  {
    label: "显示",
    tip: "会显示父级菜单",
    value: true
  },
  {
    label: "隐藏",
    tip: "不会显示父级菜单",
    value: false
  }
];

const frameLoadingOptions: Array<OptionsType> = [
  {
    label: "开启",
    tip: "有首次加载动画",
    value: true
  },
  {
    label: "关闭",
    tip: "无首次加载动画",
    value: false
  }
];

/** HTTP 方法选项（已弃用：菜单管理不再使用权限类型） */
const methodOptions: Array<OptionsType> = [
  { label: "GET", value: "GET" },
  { label: "POST", value: "POST" },
  { label: "PUT", value: "PUT" },
  { label: "PATCH", value: "PATCH" },
  { label: "DELETE", value: "DELETE" }
];

export {
  menuTypeOptions,
  showLinkOptions,
  fixedTagOptions,
  keepAliveOptions,
  hiddenTagOptions,
  showParentOptions,
  frameLoadingOptions,
  methodOptions
};
