<script setup lang="ts">
/*
 * 登录日志页"统计概览"迷你趋势 sparkline（近 7 日面积折线，无坐标轴文字）。
 *
 * 由 login/index.vue 以 defineAsyncComponent + loadEcharts() 懒加载：
 * @pureadmin/utils 的 useECharts 在组件 setup 时同步读取 globalProperties.$echarts，
 * 必须先于本组件 setup 完成注册（与 welcome 页图表组件同模式）。
 * 仅本页私用，不跨目录引用 welcome 页面私有组件；getCssVar/hexToRgba 与
 * welcome/utils.ts 同实现，刻意本地复制以避免页面间私有依赖。
 * 颜色一律运行时读取 EP CSS 变量，随 html.dark 自动适配深浅色。
 */
import { type PropType, computed, ref, watch } from "vue";
import { type UtilsEChartsOption, useDark, useECharts } from "@pureadmin/utils";

/** 趋势数据点（与 API 层 LoginTrendItem 同构，图表组件不直接依赖 API 层） */
export type TrendPoint = {
  date: string;
  count: number;
};

const props = defineProps({
  /** 近 7 日趋势，升序，可能含 0 */
  data: {
    type: Array as PropType<TrendPoint[]>,
    default: () => []
  },
  /** 图表高度（统计条内默认 48px） */
  height: {
    type: String,
    default: "48px"
  }
});

const { isDark } = useDark();

const theme = computed(() => (isDark.value ? "dark" : "light"));

const chartRef = ref();
const { setOptions } = useECharts(chartRef, {
  theme,
  renderer: "svg"
});

/** 读取根节点上的 CSS 变量值（同 welcome/utils.ts 实现） */
function getCssVar(name: string): string {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

/** hex → rgba。echarts 画布不识别 CSS 变量，注入 series 颜色前需先解析为具体色值 */
function hexToRgba(hex: string, alpha: number): string {
  const fallback = "#409eff"; // EP 默认主题色，变量缺失时兜底
  const value = /^#[0-9a-fA-F]{6}$/.test(hex) ? hex : fallback;
  const r = parseInt(value.slice(1, 3), 16);
  const g = parseInt(value.slice(3, 5), 16);
  const b = parseInt(value.slice(5, 7), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/** 组装迷你配置：纯面积折线，隐藏坐标轴文字/刻度/网格，仅保留 hover 提示 */
function buildOptions(): UtilsEChartsOption {
  const primary = getCssVar("--el-color-primary") || "#409eff";
  const textColor = getCssVar("--el-text-color-regular") || "#606266";
  const overlayBg = getCssVar("--el-bg-color-overlay") || "#ffffff";
  const overlayBorder = getCssVar("--el-border-color-light") || "#e4e7ed";

  return {
    tooltip: {
      trigger: "axis",
      backgroundColor: overlayBg,
      borderColor: overlayBorder,
      textStyle: { color: textColor }
    },
    grid: { top: 4, left: 2, right: 2, bottom: 0 },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: props.data.map(item => item.date),
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: { show: false }
    },
    yAxis: {
      type: "value",
      axisLabel: { show: false },
      splitLine: { show: false }
    },
    series: [
      {
        name: "登录次数",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 4,
        showSymbol: false,
        data: props.data.map(item => item.count),
        color: primary,
        lineStyle: { width: 1.5 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: hexToRgba(primary, 0.3) },
              { offset: 1, color: hexToRgba(primary, 0.02) }
            ]
          }
        }
      }
    ]
  };
}

setOptions(buildOptions());
watch(
  () => props.data,
  () => setOptions(buildOptions()),
  { deep: true }
);
// 主题切换：useECharts 内部会按 theme 重建实例并重放最后一次 setOptions，
// 这里再以新变量值重设一次，保证提示框颜色同步更新
watch(isDark, () => setOptions(buildOptions()));
</script>

<template>
  <div ref="chartRef" class="w-full" :style="{ height }" />
</template>
