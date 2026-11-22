<script setup lang="ts">
import { computed } from "vue";
import { useDark } from "@pureadmin/utils";
import { IconifyIconOffline } from "@/components/ReIcon";
import { ReNormalCountTo } from "@/components/ReCountTo";
import { statCardProps, type StatTrend } from "./types";

defineOptions({
  name: "ReStatCard"
});

const props = defineProps(statCardProps);

const { isDark } = useDark();

/** 趋势标签语义色映射：上升/下降/持平 */
const TREND_TAG_TYPES: Record<
  StatTrend["type"],
  "success" | "danger" | "info"
> = {
  up: "success",
  down: "danger",
  flat: "info"
};

/** 图标块样式：浅色用传入的淡色底，深色转透明（描边由 .dark 下的 inset 阴影接管），对齐原 line-card 行为 */
const iconBlockStyle = computed(() => ({
  backgroundColor: isDark.value
    ? "transparent"
    : props.iconBg || "var(--el-color-primary-light-9)",
  color: props.iconColor || "var(--el-color-primary)"
}));
</script>

<template>
  <el-card class="re-stat-card" shadow="never">
    <div class="flex-bc">
      <span class="re-stat-card__title">{{ title }}</span>
      <el-tag
        v-if="trend"
        size="small"
        effect="light"
        round
        :type="TREND_TAG_TYPES[trend.type]"
      >
        {{ trend.text }}
      </el-tag>
    </div>
    <div
      class="size-8 mt-3 flex-c rounded-md re-stat-card__icon"
      :style="iconBlockStyle"
    >
      <IconifyIconOffline :icon="icon" width="18" height="18" />
    </div>
    <div class="flex items-baseline mt-3">
      <ReNormalCountTo
        :duration="duration"
        :startVal="0"
        :endVal="value"
        fontSize="1.7em"
      />
      <span v-if="suffix" class="ml-1 text-sm text-text_color_regular">
        {{ suffix }}
      </span>
    </div>
    <p v-if="subText" class="mt-1 text-xs text-text_color_regular">
      {{ subText }}
    </p>
  </el-card>
</template>

<style lang="scss" scoped>
/* 无边框卡风格：与原 line-card 一致，靠卡片底色与阴影分层 */
.el-card {
  --el-card-border-color: none;
}

.re-stat-card__title {
  font-size: 14px;
  font-weight: 500;
}

/* 深色模式：图标块透明底需要细描边保持层次 */
.dark .re-stat-card__icon {
  box-shadow: inset 0 0 0 1px var(--el-border-color-lighter);
}
</style>
