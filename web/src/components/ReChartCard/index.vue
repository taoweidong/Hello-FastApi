<script setup lang="ts">
import { type PropType, computed } from "vue";

defineOptions({
  name: "ReChartCard"
});

const props = defineProps({
  /** 卡片标题 */
  title: {
    type: String,
    required: true
  },
  /** 可选副标题（标题右侧灰色小字） */
  subtitle: {
    type: String,
    default: ""
  },
  /** 内容区最小高度：数字按 px 处理，字符串原样透传（如 "50vh"） */
  minHeight: {
    type: [Number, String] as PropType<number | string>,
    default: 340
  }
});

/** 内容区 min-height：数字转 px，字符串直接透传 */
const bodyStyle = computed(() => ({
  minHeight:
    typeof props.minHeight === "number"
      ? `${props.minHeight}px`
      : props.minHeight
}));
</script>

<template>
  <el-card class="re-chart-card" shadow="never">
    <div class="flex justify-between items-center re-chart-card__header">
      <div class="flex items-baseline">
        <span class="re-chart-card__title">{{ title }}</span>
        <span v-if="subtitle" class="ml-2 text-xs text-text_color_regular">
          {{ subtitle }}
        </span>
      </div>
      <!-- 右上角操作区：刷新按钮、时间范围切换等 -->
      <div class="re-chart-card__actions">
        <slot name="actions" />
      </div>
    </div>
    <!-- 图表 / 表格等内容本体 -->
    <div class="re-chart-card__body" :style="bodyStyle">
      <slot />
    </div>
  </el-card>
</template>

<style lang="scss" scoped>
/* 无边框卡风格：与原 line-card 一致；内边距统一走间距令牌 */
.el-card {
  --el-card-border-color: none;
  --el-card-padding: var(--pure-space-5);
}

.re-chart-card__header {
  padding-bottom: var(--pure-space-3);
}

.re-chart-card__title {
  font-size: 14px;
  font-weight: 500;
}

.re-chart-card__body {
  padding-top: var(--pure-space-2);
}
</style>
