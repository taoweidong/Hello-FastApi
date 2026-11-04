<template>
  <el-config-provider :locale="currentLocale">
    <router-view />
    <ReDialog />
    <ReDrawer />
  </el-config-provider>
</template>

<script lang="ts">
import { checkVersion } from "version-rocket";
import { ElConfigProvider } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import { useGlobal, useWatermark } from "@pureadmin/utils";
import {
  defineComponent,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount
} from "vue";
import { ReDialog, closeAllDialog } from "@/components/ReDialog";
import { ReDrawer, closeAllDrawer } from "@/components/ReDrawer";
import { realtime } from "@/utils/websocket";
import en from "element-plus/es/locale/lang/en";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import plusEn from "plus-pro-components/es/locale/lang/en";
import plusZhCn from "plus-pro-components/es/locale/lang/zh-cn";

export default defineComponent({
  name: "app",
  components: {
    [ElConfigProvider.name]: ElConfigProvider,
    ReDialog,
    ReDrawer
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const { setWatermark, clear } = useWatermark();
    const { $storage } = useGlobal<GlobalPropertiesApi>();
    const watermarkEnable = computed(() => $storage.configure?.watermark);
    const watermarkText = computed(() => $storage.configure?.watermarkText);
    const currentLocale = computed(() => {
      return $storage.locale?.locale === "zh"
        ? { ...zhCn, ...plusZhCn }
        : { ...en, ...plusEn };
    });

    router.beforeEach(() => {
      closeAllDialog();
      closeAllDrawer();
    });

    // 页面挂载（含刷新场景）即有 token 则建立实时消息连接；
    // 登入/登出由 user store 控制 start/stop，二者互补不会重复连接。
    // 监听页面卸载/隐藏时主动断开，避免 WS 经 dev 代理在后端侧累积半开连接，
    // 否则多页面场景（如 E2E）会偶发挤占同代理的 HTTP 请求（如更新资料）。
    // 注意：隐藏时 stop、恢复可见时 start 必须成对——只 stop 不 start 的话，
    // 用户每次切走标签页再切回，实时通知会静默失效直到刷新页面。
    // 监听器必须用具名函数成对注册/移除，匿名函数会导致监听器泄漏。
    const stopRealtimeOnLeave = () => realtime.stop();
    const handleVisibilityChange = () => {
      if (document.hidden) {
        realtime.stop();
      } else {
        realtime.start();
      }
    };
    onMounted(() => {
      realtime.start();
      window.addEventListener("pagehide", stopRealtimeOnLeave);
      document.addEventListener("visibilitychange", handleVisibilityChange);
    });
    onBeforeUnmount(() => {
      window.removeEventListener("pagehide", stopRealtimeOnLeave);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      realtime.stop();
    });

    watch(
      [watermarkEnable, watermarkText, () => route.name],
      async ([enable, text, name]) => {
        await nextTick();
        if (enable && name !== "Login") {
          setWatermark(text, { verticalOffset: 170 });
        } else {
          clear();
        }
      },
      {
        immediate: true
      }
    );

    return {
      currentLocale
    };
  },
  beforeCreate() {
    const { version, name: title } = __APP_INFO__.pkg;
    const { VITE_PUBLIC_PATH, MODE } = import.meta.env;
    // https://github.com/guMcrey/version-rocket/blob/main/README.zh-CN.md#api
    if (MODE === "production") {
      // 版本实时更新检测，只作用于线上环境
      checkVersion(
        // config
        {
          // 5分钟检测一次版本
          pollingTime: 300000,
          localPackageVersion: version,
          originVersionFileUrl: `${location.origin}${VITE_PUBLIC_PATH}version.json`
        },
        // options
        {
          title,
          description: "检测到新版本",
          buttonText: "立即更新"
        }
      );
    }
  }
});
</script>
