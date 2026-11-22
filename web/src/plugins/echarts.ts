/*
 * echarts 懒加载工具模块（原为 main.ts 启动即注册的全局插件）。
 *
 * 改造原因：全站只有 welcome 首页用图表，原先 main.ts 里 use(useEcharts)
 * 会在首屏就加载 echarts（Canvas+SVG 双渲染器 + 一堆未用到的组件），
 * 拖慢首屏。现改为：welcome 首页用 defineAsyncComponent 包裹图表组件，
 * 渲染前才动态 import echarts 并按需注册所需模块（见 loadEcharts）。
 *
 * 注册结果仍挂到 globalProperties.$echarts——@pureadmin/utils 的 useECharts
 * 在组件 setup 时同步读取该属性，因此必须保证图表组件 setup 前 loadEcharts 已完成。
 */
import { getCurrentInstance } from "vue";

type EchartsModule = typeof import("echarts/core");

let loadPromise: Promise<EchartsModule> | null = null;

/**
 * 动态加载 echarts 并按需注册所需模块；多次调用共享同一次加载。
 *
 * 必须在图表组件 setup 之前 await 完成（useECharts 会在 setup 时同步
 * 捕获 globalProperties.$echarts，晚挂载会报"echarts未绑定到globalProperties"）。
 * 注意 getCurrentInstance 只在同步执行阶段有效，需先取出 globalProperties。
 */
export function loadEcharts(): Promise<EchartsModule> {
  loadPromise ??= (async () => {
    const globalProps =
      getCurrentInstance()?.appContext.config.globalProperties;
    const [echarts, charts, renderers, components] = await Promise.all([
      import("echarts/core"),
      import("echarts/charts"),
      import("echarts/renderers"),
      import("echarts/components")
    ]);
    echarts.use([
      charts.BarChart, // ChartBar 柱状图 / ChartRound 极坐标进度条（series type: "bar"）
      charts.LineChart, // ChartLine 折线图
      // SVG 渲染器保留：ChartLine / ChartRound 明确传了 renderer: "svg"
      renderers.CanvasRenderer,
      renderers.SVGRenderer,
      components.GridComponent, // ChartBar / ChartLine 的 xAxis、yAxis、grid
      components.TitleComponent, // ChartRound 的 title
      components.PolarComponent, // ChartRound 的 polar、angleAxis、radiusAxis
      components.LegendComponent, // ChartBar 的 legend
      components.TooltipComponent // ChartBar 的 tooltip
    ]);
    // 挂到 globalProperties.$echarts，供 @pureadmin/utils 的 useECharts 使用
    if (globalProps) {
      globalProps.$echarts = echarts;
    }
    return echarts;
  })();
  return loadPromise;
}
