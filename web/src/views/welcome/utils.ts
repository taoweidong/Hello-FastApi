export { useDark } from "@pureadmin/utils";
export { default as dayjs } from "dayjs";

/** 读取根节点上的 CSS 变量值（EP 主题变量随 html.dark 自动切换，无需手动感知暗色） */
export function getCssVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

/** hex → rgba。echarts 画布不识别 CSS 变量，注入 series 颜色前需先解析为具体色值 */
export function hexToRgba(hex: string, alpha: number): string {
  const fallback = "#409eff"; // EP 默认主题色，变量缺失时兜底
  const value = /^#[0-9a-fA-F]{6}$/.test(hex) ? hex : fallback;
  const r = parseInt(value.slice(1, 3), 16);
  const g = parseInt(value.slice(3, 5), 16);
  const b = parseInt(value.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** 十六进制颜色线性插值：ratio 越大越接近 b */
function mixHex(a: string, b: string, ratio: number): string {
  const parse = (hex: string) => {
    const value = /^#[0-9a-fA-F]{6}$/.test(hex) ? hex : "#409eff";
    return [
      parseInt(value.slice(1, 3), 16),
      parseInt(value.slice(3, 5), 16),
      parseInt(value.slice(5, 7), 16)
    ];
  };
  const [r1, g1, b1] = parse(a);
  const [r2, g2, b2] = parse(b);
  const channel = (x: number, y: number) =>
    Math.round(x + (y - x) * ratio)
      .toString(16)
      .padStart(2, "0");
  return `#${channel(r1, r2)}${channel(g1, g2)}${channel(b1, b2)}`;
}

/**
 * 基于 EP 主题色及其衍生色变量生成 count 个色板色。
 *
 * 色板来源（均随 html.dark 在深色模式下自动变暗，深浅色无需两套配置）：
 * [primary, light-3, light-5, light-7, dark-2, light-9]；
 * 条目数不足时在相邻色之间线性插值补齐（最多可扩展到 11 色，覆盖 TOP8 饼图）。
 */
export function buildPrimaryPalette(count: number): string[] {
  const base = getCssVar("--el-color-primary");
  const palette: string[] = [/^#[0-9a-fA-F]{6}$/.test(base) ? base : "#409eff"];
  const derivedVars = [
    "--el-color-primary-light-3",
    "--el-color-primary-light-5",
    "--el-color-primary-light-7",
    "--el-color-primary-dark-2",
    "--el-color-primary-light-9"
  ];
  for (const name of derivedVars) {
    const value = getCssVar(name);
    if (/^#[0-9a-fA-F]{6}$/.test(value)) {
      palette.push(value);
    }
  }
  // 兜底：衍生变量全部缺失时退化为主题色 alpha 递减
  if (palette.length < 2) {
    return Array.from({ length: Math.max(count, 1) }, (_, i) =>
      hexToRgba(
        palette[0],
        Math.max(1 - i * (0.75 / Math.max(count - 1, 1)), 0.2)
      )
    );
  }
  while (palette.length < count) {
    const inserts: string[] = [];
    for (
      let i = 0;
      i < palette.length - 1 && palette.length + inserts.length < count;
      i++
    ) {
      inserts.push(mixHex(palette[i], palette[i + 1], 0.5));
    }
    palette.push(...inserts);
  }
  return palette.slice(0, Math.max(count, 1));
}
