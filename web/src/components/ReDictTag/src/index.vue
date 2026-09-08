<script setup lang="ts">
import { computed } from "vue";
import type { DictOption } from "@/composables/useDict";

defineOptions({
  name: "ReDictTag"
});

const props = withDefaults(
  defineProps<{
    /** 字典项列表（通常来自 useDict） */
    options: Array<DictOption>;
    /** 待渲染的字典值 */
    value?: string | number | null;
    /** el-tag 类型，缺省为 primary */
    tagType?: "" | "success" | "warning" | "info" | "danger" | "primary";
    /** el-tag 尺寸 */
    size?: "large" | "default" | "small";
    /** 字典未命中时的回退显示 */
    fallback?: string;
  }>(),
  {
    value: null,
    tagType: "primary",
    size: "default",
    fallback: ""
  }
);

/** 按值匹配字典项（值统一转字符串比较，兼容数字/字符串） */
const matched = computed(() => {
  if (props.value === null || props.value === undefined) return undefined;
  return props.options.find(item => String(item.value) === String(props.value));
});

/** 未命中时的展示文本 */
const fallbackText = computed(() => {
  if (props.value === null || props.value === undefined || props.value === "") {
    return props.fallback;
  }
  return props.fallback || String(props.value);
});
</script>

<template>
  <el-tag
    v-if="matched"
    :type="tagType || undefined"
    :size="size"
    effect="plain"
  >
    {{ matched.label }}
  </el-tag>
  <span v-else>{{ fallbackText }}</span>
</template>
