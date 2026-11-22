<script setup lang="ts">
import { useI18n } from "vue-i18n";
import LayFrame from "../lay-frame/index.vue";
import LayFooter from "../lay-footer/index.vue";
import { useTags } from "@/layout/hooks/useTag";
import { useGlobal, isNumber } from "@pureadmin/utils";
import BackTopIcon from "@/assets/svg/back_top.svg?component";
import { h, computed, Transition, defineComponent } from "vue";
import { usePermissionStoreHook } from "@/store/modules/permission";
import { loadAnimateCss } from "@/utils/animate";

const props = defineProps({
  fixedHeader: Boolean
});

const { t } = useI18n();
const { tagsStyle } = useTags();
const { $storage, $config } = useGlobal<GlobalPropertiesApi>();

const isKeepAlive = computed(() => {
  return $config?.KeepAlive;
});

const transitions = computed(() => {
  return route => {
    return route.meta.transition;
  };
});

const hideTabs = computed(() => {
  return $storage?.configure.hideTabs;
});

const hideFooter = computed(() => {
  return $storage?.configure.hideFooter;
});

const stretch = computed(() => {
  return $storage?.configure.stretch;
});

const getMainWidth = computed(() => {
  // 原先 stretch 为 false/unset 时两支都返回 "100%"，冗余三元已合并
  return isNumber(stretch.value) ? stretch.value + "px" : "100%";
});

/*
 * 顶部导航区高度单一事实来源：tokens.scss 的 --pure-navbar-height /
 * --pure-header-height(-chrome) / --pure-content-min-height（推导见该文件注释）。
 * 旧值核对：隐藏页签 48px；显示页签 普通 81px（48+33）、chrome 85px（48+37）；
 * 非固定头 min-height 减项 隐藏页签 48px（= --pure-navbar-height）、
 * 显示页签 86px（= --pure-content-min-height），逐像素等价。
 * 注：旧实现里 hideTabs && layout 与 hideTabs && !layout 输出完全相同，
 * 已合并为与 layout 无关的单一分支。
 */
const getSectionStyle = computed(() => {
  return [
    hideTabs.value
      ? "padding-top: var(--pure-navbar-height);"
      : tagsStyle.value == "chrome"
        ? "padding-top: var(--pure-header-height-chrome);"
        : "padding-top: var(--pure-header-height);",
    props.fixedHeader
      ? ""
      : `padding-top: 0; min-height: ${
          // 旧值核对：隐藏页签 calc(100vh - 48px)；显示页签 calc(100vh - 86px)
          hideTabs.value
            ? "calc(100vh - var(--pure-navbar-height))"
            : "var(--pure-content-min-height)"
        };`
  ];
});

const transitionMain = defineComponent({
  props: {
    route: {
      type: undefined,
      required: true
    }
  },
  render() {
    const transitionName =
      transitions.value(this.route)?.name || "fade-transform";
    const enterTransition = transitions.value(this.route)?.enterTransition;
    const leaveTransition = transitions.value(this.route)?.leaveTransition;
    /*
     * animate.css 按需加载：仅当路由 meta 声明了 enter/leaveTransition
     * （animate__ 前缀类名）时才动态 import；未声明时永不加载。
     * loadAnimateCss 内部有模块级 once 标志，render 多次执行也只加载一次。
     */
    if (enterTransition || leaveTransition) {
      loadAnimateCss();
    }
    return h(
      Transition,
      {
        name: enterTransition ? "pure-classes-transition" : transitionName,
        enterActiveClass: enterTransition
          ? `animate__animated ${enterTransition}`
          : undefined,
        leaveActiveClass: leaveTransition
          ? `animate__animated ${leaveTransition}`
          : undefined,
        mode: "out-in"

        // 不再启用 appear：首屏无需播放路由切换动画，避免无意义的入场动效
      },
      {
        default: () => [this.$slots.default()]
      }
    );
  }
});
</script>

<template>
  <section
    :class="[fixedHeader ? 'app-main' : 'app-main-nofixed-header']"
    :style="getSectionStyle"
  >
    <router-view>
      <template #default="{ Component, route }">
        <LayFrame :currComp="Component" :currRoute="route">
          <template #default="{ Comp, fullPath, frameInfo }">
            <el-scrollbar
              v-if="fixedHeader"
              :wrap-style="{
                display: 'flex',
                'flex-wrap': 'wrap',
                'max-width': getMainWidth,
                margin: '0 auto',

                /*
                 * 原先是 `transition: all 300ms`。侧边栏收起时这里实际只有
                 * max-width 在变，写 all 会把 margin / display 等无关属性
                 * 一并纳入过渡计算，每次折叠都触发额外的样式重算。
                 * 收窄到 max-width，并把时长/缓动统一到设计令牌。
                 */
                transition:
                  'max-width var(--pure-duration-slow) var(--pure-ease-standard)'
              }"
              :view-style="{
                display: 'flex',
                flex: '1',
                overflow: 'hidden',
                'flex-direction': 'column',
                'min-height': '0'
              }"
            >
              <el-backtop
                :title="t('buttons.pureBackTop')"
                target=".app-main .el-scrollbar__wrap"
              >
                <BackTopIcon />
              </el-backtop>
              <div class="grow">
                <!--
                  组件 key：普通页面用 route.path（原先的 fullPath 会让仅 query
                  变化的导航强制重建实例；全仓已确认没有"同一路由不同 query 需要
                  独立实例"的用法）；iframe 多页签（frameSrc）仍按 fullPath 区分，
                  否则 compList 中其它 frame 实例会因 key 随当前路由漂移被销毁。
                -->
                <transitionMain :route="route">
                  <keep-alive
                    v-if="isKeepAlive"
                    :include="usePermissionStoreHook().cachePageList"
                  >
                    <component
                      :is="Comp"
                      :key="frameInfo?.frameSrc ? fullPath : route.path"
                      :frameInfo="frameInfo"
                      class="main-content"
                    />
                  </keep-alive>
                  <component
                    :is="Comp"
                    v-else
                    :key="frameInfo?.frameSrc ? fullPath : route.path"
                    :frameInfo="frameInfo"
                    class="main-content"
                  />
                </transitionMain>
              </div>
              <LayFooter v-if="!hideFooter" />
            </el-scrollbar>
            <div v-else class="grow">
              <transitionMain :route="route">
                <keep-alive
                  v-if="isKeepAlive"
                  :include="usePermissionStoreHook().cachePageList"
                >
                  <component
                    :is="Comp"
                    :key="frameInfo?.frameSrc ? fullPath : route.path"
                    :frameInfo="frameInfo"
                    class="main-content"
                  />
                </keep-alive>
                <component
                  :is="Comp"
                  v-else
                  :key="frameInfo?.frameSrc ? fullPath : route.path"
                  :frameInfo="frameInfo"
                  class="main-content"
                />
              </transitionMain>
            </div>
          </template>
        </LayFrame>
      </template>
    </router-view>

    <!-- 页脚 -->
    <LayFooter v-if="!hideFooter && !fixedHeader" />
  </section>
</template>

<style scoped>
.app-main {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100vh;
  overflow-x: hidden;
}

.app-main-nofixed-header {
  position: relative;
  display: flex;
  flex-direction: column;
  width: 100%;
}

.main-content {
  flex: 1;

  /*
   * 外边距统一由 style/element-plus.scss 的 .main-content token 版本接管
   * （含 !important），此处不再重复声明，避免两处各改一半。
   */
}
</style>
