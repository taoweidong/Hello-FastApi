/**
 * 系统管理公共渲染工具
 *
 * 提供 Segmented 渲染函数、Switch 渲染函数等 TSX 工具
 */
import { h } from "vue";
import type { OptionsType } from "@/components/ReSegmented";

/** 为 Segmented 组件提供选项渲染 */
export function renderOption(options: ReadonlyArray<OptionsType>) {
  return options.map(opt => ({
    label: opt.label,
    value: opt.value,
    tip: opt.tip
  }));
}

/** 渲染 el-switch 组件（启用/停用） */
export function renderSwitch(value: boolean, style?: Record<string, string>) {
  return h("span", { style }, value ? "启用" : "停用");
}

/** 渲染菜单类型 tag */
export function renderMenuTypeTag(type: number, size: string = "default") {
  const typeMap: Record<number, { tagType: string; text: string }> = {
    0: { tagType: "primary", text: "目录" },
    1: { tagType: "warning", text: "页面" },
    2: { tagType: "info", text: "权限" }
  };
  const info = typeMap[type] ?? { tagType: "", text: "未知" };
  return h(
    "el-tag" as any,
    { size, type: info.tagType, effect: "plain" },
    () => info.text
  );
}
