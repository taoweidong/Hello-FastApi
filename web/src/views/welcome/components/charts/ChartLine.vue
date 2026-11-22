<script setup lang="ts">
/*
 * 登录趋势面积折线图（真实数据驱动，替代原 welcome 假数据小折线）。
 *
 * 由页面 defineAsyncComponent + loadEcharts() 懒加载（echarts 按需注册见 plugins/echarts.ts）。
 * 颜色一律运行时读取 EP CSS 变量：坐标轴/文字/分割线随 html.dark 自动切换，
 * 主题色取 --el-color-primary，面积渐变由其 rgba 派生，深浅色共用一套配置。
 */
import { type PropType, computed, ref, watch } from "vue";
import { type UtilsEChartsOption, useDark, useECharts } from "@pureadmin/utils";
import { getCssVar, hexToRgba } from "../../utils";

/** 趋势数据点（与 API 层 LoginTrendItem 同构，图表组件不直接依赖 API 层） */
export type TrendPoint = {
  date: string;
  count: number;
};

const props = defineProps({
  /** 近 7 日登录趋势，升序，可能含 0 */
  data: {
    type: Array as PropType<TrendPoint[]>,
    default: () => []
  },
  /** 图表高度 */
  height: {
    type: String,
    default: "300px"
  }
});

const { isDark } = useDark();

const theme = computed(() => (isDark.value ? "dark" : "light"));

const chartRef = ref();
const { setOptions } = useECharts(chartRef, {
  theme,
  renderer: "svg"
});

/** 组装配置：依赖 isDark 与 props.data，二者变化时整体重设 */
function buildOptions(): UtilsEChartsOption {
  const primary = getCssVar("--el-color-primary") || "#409eff";
  const textColor = getCssVar("--el-text-color-regular") || "#606266";
  const lineColor = getCssVar("--el-border-color-lighter") || "#e4e7ed";
  const overlayBg = getCssVar("--el-bg-color-overlay") || "#ffffff";
  const overlayBorder = getCssVar("--el-border-color-light") || "#e4e7ed";

  return {
    // 尺寸联动容器：挂在 ReChartCard 内容区上，随卡片布局变化 resize
    container: ".re-chart-card__body",
    tooltip: {
      trigger: "axis",
      backgroundColor: overlayBg,
      borderColor: overlayBorder,
      textStyle: { color: textColor }
    },
    grid: {
      top: 30,
      left: 20,
      right: 20,
      bottom: 10,
      containLabel: true
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: props.data.map(item => item.date),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: lineColor } },
      axisLabel: { color: textColor }
    },
    yAxis: {
      type: "value",
      minInterval: 1, // 次数为整数，避免坐标轴出现小数刻度
      axisLabel: { color: textColor },
      splitLine: { lineStyle: { type: "dashed", color: lineColor } }
    },
    series: [
      {
        name: "登录次数",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        showSymbol: false,
        data: props.data.map(item => item.count),
        color: primary,
        lineStyle: {
          width: 3,
          shadowOffsetY: 6,
          shadowBlur: 9,
          shadowColor: hexToRgba(primary, 0.35)
        },
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
// 这里再以新变量值重设一次，保证坐标轴/文字颜色同步更新
watch(isDark, () => setOptions(buildOptions()));
</script>

<template>
  <div ref="chartRef" class="w-full" :style="{ height }" />
</template>
