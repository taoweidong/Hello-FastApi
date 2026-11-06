<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { emitter } from "@/utils/mitt";
import { onClickOutside } from "@vueuse/core";
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { useDataThemeChange } from "@/layout/hooks/useDataThemeChange";
import CloseIcon from "~icons/ep/close";

const target = ref(null);
const show = ref<Boolean>(false);

const iconClass = computed(() => {
  return [
    "size-5.5",
    "flex-c",
    "outline-hidden",
    "rounded-sm",
    "cursor-pointer",
    "transition-colors",
    "hover:bg-[#0000000f]",
    "dark:hover:bg-[#ffffff1f]",
    "dark:hover:text-[#ffffffd9]"
  ];
});

const { t } = useI18n();
const { onReset } = useDataThemeChange();

/**
 * 读取 CSS 变量中的层级数值。
 * tippy 的 zIndex 只接受 number，无法直接写 var(--pure-z-tooltip)，
 * 这里在 setup 阶段解析一次，值与 tokens.scss 中的层级刻度保持同源。
 */
function readCssVarNumber(name: string, fallback: number): number {
  if (typeof window === "undefined") return fallback;
  const raw = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  const value = Number.parseInt(raw, 10);
  return Number.isFinite(value) ? value : fallback;
}

/** 提示气泡需盖住设置面板本身（--pure-z-top），故用更高级的 --pure-z-tooltip */
const tooltipZIndex = readCssVarNumber("--pure-z-tooltip", 4100);

onClickOutside(target, (event: any) => {
  if (event.clientX > target.value.offsetLeft) return;
  show.value = false;
});

onMounted(() => {
  emitter.on("openPanel", () => {
    show.value = true;
  });
});

onBeforeUnmount(() => {
  // 解绑`openPanel`公共事件，防止多次触发
  emitter.off("openPanel");
});
</script>

<template>
  <div :class="{ show }">
    <div class="right-panel-background" />
    <div ref="target" class="right-panel bg-bg_color">
      <div
        class="flex-bc py-3 px-5 border-0 border-l border-solid border-(--pure-border-color)"
      >
        <h4 class="dark:text-white">
          {{ t("panel.pureSystemSet") }}
        </h4>
        <span
          v-tippy="{
            content: t('panel.pureCloseSystemSet'),
            placement: 'bottom-start',
            zIndex: tooltipZIndex
          }"
          :class="iconClass"
        >
          <IconifyIconOffline
            class="dark:text-white"
            width="18px"
            height="18px"
            :icon="CloseIcon"
            @click="show = !show"
          />
        </span>
      </div>
      <el-scrollbar
        class="border-y border-l border-r-0 border-solid border-(--pure-border-color) h-[calc(100vh-104px)]!"
      >
        <slot />
      </el-scrollbar>

      <div
        class="flex justify-end p-3 border-0 border-l border-solid border-(--pure-border-color)"
      >
        <el-button
          v-tippy="{
            content: t('panel.pureClearCacheAndToLogin'),
            placement: 'left-start',
            zIndex: tooltipZIndex
          }"
          type="danger"
          text
          bg
          @click="onReset"
        >
          {{ t("panel.pureClearCache") }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.right-panel-background {
  position: fixed;
  top: 0;
  left: 0;
  z-index: -1;
  background: rgb(0 0 0 / 20%);
  opacity: 0;
  transition: opacity var(--pure-duration-slow) var(--pure-ease-emphasized);
}

.right-panel {
  position: fixed;
  top: 0;
  right: 0;

  /* 原为魔法值 40000，纳入 tokens.scss 的层级刻度：全局浮层最高级 */
  z-index: var(--pure-z-top);
  width: 100%;
  max-width: 280px;
  box-shadow: var(--pure-shadow-3);
  transform: translate(100%);
  transition: transform var(--pure-duration-panel) var(--pure-ease-emphasized);
}

.show {
  transition: opacity var(--pure-duration-slow) var(--pure-ease-emphasized);

  .right-panel-background {
    /* 原为 20000；遮罩应压住内容但低于面板本身 */
    z-index: calc(var(--pure-z-top) - 1);
    width: 100%;
    height: 100%;
    opacity: 1;
  }

  .right-panel {
    transform: translate(0);
  }
}
</style>
