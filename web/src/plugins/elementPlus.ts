// 按需引入element-plus（该方法稳定且明确。当然也支持：https://element-plus.org/zh-CN/guide/quickstart.html#%E6%8C%89%E9%9C%80%E5%AF%BC%E5%85%A5）
//
// 组件注册表裁剪说明（2025 资源瘦身批次）：
// - 原先注册了 element-plus 导出的全部组件（约 100 个），其中大量从未使用，
//   却会进入首屏 bundle（JS 注册本身就把对应组件代码拉进 vendor）；
// - 现仅保留 src/ 下实际使用的组件（逐个 grep 过模板 kebab `el-xxx` 与
//   tsx Pascal `ElXxx` 两种写法，零引用的注册全部移除）；
// - 后续新增页面用到未注册组件时，在此数组补一行即可；
// - CSS 仍走 main.ts 里的 `element-plus/dist/index.css` 全量引入（不做按需）：
//   CSS 按需需要迁移到 unplugin-vue-components + unplugin-auto-import 方案，
//   改动面大，本次瘦身不做（见 AGENTS.md/任务说明）。
import type { App, Component } from "vue";
import {
  ElAlert,
  ElAutocomplete,
  ElAside,
  ElAvatar,
  ElBacktop,
  ElBadge,
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElCard,
  ElCascader,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElConfigProvider,
  ElContainer,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElImage,
  ElInput,
  ElInputNumber,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElPagination,
  ElPopconfirm,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioGroup,
  ElResult,
  ElRow,
  ElScrollbar,
  ElSelect,
  ElOption,
  ElSkeleton,
  ElSpace,
  ElSubMenu,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTabPane,
  ElTag,
  ElText,
  ElTimeline,
  ElTimelineItem,
  ElTooltip,
  ElTree,
  ElTreeV2,
  ElUpload,
  /**
   * 插件/服务说明：
   * - ElLoading 必须保留——15 个文件在模板里用了 `v-loading` 指令，
   *   该指令靠 app.use(ElLoading) 全局注册；
   * - ElMessage / ElMessageBox / ElNotification 是命令式 API，代码里
   *   都是直接 import（如 utils/message.ts），不依赖全局注册，故不再
   *   app.use（原本只是挂 $message/$msgbox/$notify 到 globalProperties，
   *   全仓无一处这样使用）；
   * - ElInfiniteScroll / ElPopoverDirective（v-infinite-scroll / v-popover
   *   指令）全仓零使用，移除。
   */
  ElLoading
} from "element-plus";

const components = [
  ElAlert,
  ElAutocomplete,
  ElAside,
  ElAvatar,
  ElBacktop,
  ElBadge,
  ElBreadcrumb,
  ElBreadcrumbItem,
  ElButton,
  ElCard,
  ElCascader,
  ElCheckbox,
  ElCheckboxGroup,
  ElCol,
  ElConfigProvider,
  ElContainer,
  ElDatePicker,
  ElDescriptions,
  ElDescriptionsItem,
  ElDialog,
  ElDivider,
  ElDrawer,
  ElDropdown,
  ElDropdownItem,
  ElDropdownMenu,
  ElEmpty,
  ElForm,
  ElFormItem,
  ElIcon,
  ElImage,
  ElInput,
  ElInputNumber,
  ElMain,
  ElMenu,
  ElMenuItem,
  ElPagination,
  ElPopconfirm,
  ElPopover,
  ElProgress,
  ElRadio,
  ElRadioGroup,
  ElResult,
  ElRow,
  ElScrollbar,
  ElSelect,
  ElOption,
  ElSkeleton,
  ElSpace,
  ElSubMenu,
  ElSwitch,
  ElTable,
  ElTableColumn,
  ElTabs,
  ElTabPane,
  ElTag,
  ElText,
  ElTimeline,
  ElTimelineItem,
  ElTooltip,
  ElTree,
  ElTreeV2,
  ElUpload
];

const plugins = [
  // v-loading 指令依赖此注册（v-infinite-scroll / v-popover 已确认零使用未注册）
  ElLoading
];

/** 按需引入`element-plus` */
export function useElementPlus(app: App) {
  // 全局注册组件
  components.forEach((component: Component) => {
    app.component(component.name, component);
  });
  // 全局注册插件
  plugins.forEach(plugin => {
    app.use(plugin);
  });
}
