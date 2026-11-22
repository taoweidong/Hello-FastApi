<script setup lang="ts">
/*
 * 操作模块分布环形饼图（真实数据驱动）。
 *
 * 由页面 defineAsyncComponent + loadEcharts() 懒加载。
 * 色板运行时读取 EP 主题色衍生变量（见 buildPrimaryPalette），
 * 刻度文字/图例/悬浮层颜色随 html.dark 自动切换。
 */
import { type PropType, computed, ref, watch } from "vue";
import { type UtilsEChartsOption, useDark, useECharts } from "@pureadmin/utils";
import { buildPrimaryPalette, getCssVar } from "../../utils";

/** 分布数据点（与 API 层 OpDistItem 同构，图表组件不直接依赖 API 层） */
export type DistPoint = {
  module: string;
  count: number;
};

const props = defineProps({
  /** 操作模块分布（TOP8，降序） */
  data: {
    type: Array as PropType<DistPoint[]>,
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
  const textColor = getCssVar("--el-text-color-regular") || "#606266";
  const overlayBg = getCssVar("--el-bg-color-overlay") || "#ffffff";
  const overlayBorder = getCssVar("--el-border-color-light") || "#e4e7ed";
  const bg = getCssVar("--el-bg-color") || "#ffffff";
  // 扇区描边用卡片底色，形成分瓣的留白间隙；深浅色自动适配
  const palette = buildPrimaryPalette(Math.max(props.data.length, 4));

  return {
    // 尺寸联动容器：挂在 ReChartCard 内容区上，随卡片布局变化 resize
    container: ".re-chart-card__body",
    tooltip: {
      trigger: "item",
      backgroundColor: overlayBg,
      borderColor: overlayBorder,
      textStyle: { color: textColor },
      valueFormatter: (value: number) => `${value} 次`
    },
    legend: {
      type: "scroll",
      bottom: 0,
      left: "center",
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 10,
      textStyle: { color: textColor }
    },
    series: [
      {
        name: "操作模块分布",
        type: "pie",
        radius: ["44%", "68%"],
        center: ["50%", "44%"],
        avoidLabelOverlap: true,
        label: { show: false }, // 模块名交给图例与悬浮层，避免窄卡内标签互相挤压
        itemStyle: {
          borderColor: bg,
          borderWidth: 2,
          borderRadius: 4
        },
        emphasis: {
          scaleSize: 6
        },
        data: props.data.map((item, index) => ({
          name: item.module,
          value: item.count,
          itemStyle: { color: palette[index % palette.length] }
        }))
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
// 这里再以新变量值重设一次，保证图例/悬浮层颜色同步更新
watch(isDark, () => setOptions(buildOptions()));
</script>

<template>
  <div ref="chartRef" class="w-full" :style="{ height }" />
</template>
