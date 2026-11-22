import type { iconType } from "./types";
import { h, defineComponent, type Component } from "vue";
import { FontIcon, IconifyIconOnline, IconifyIconOffline } from "../index";
import { OFFLINE_ICON_NAMES } from "./offlineIconNames";

const ifReg = /^IF-/;
const svgReg = /^\s*<svg[\s>]/;
const svgCache = new Map<string, string>();
const imgReg = /^(https?:\/\/|\/\/|data:image\/)/;

/*
 * 在线回退开关：
 * - dev 环境默认允许在线回退（便于预览未预置图标）；
 * - 生产构建默认禁止（避免运行时依赖 api.iconify.design）；
 * - 显式设置 VITE_ICON_ONLINE_FALLBACK=true 时任何环境都强制开启。
 *   import.meta.env 的值在运行时是字符串（.env 里写 true），故用字符串比较；
 *   wrapperEnv 构建期转换出的 boolean true 也兼容（String(true) === "true"）。
 */
const allowOnlineFallback =
  String(import.meta.env.VITE_ICON_ONLINE_FALLBACK) === "true" ||
  !import.meta.env.PROD;

let onlineIconWarned = false;
/** 未预置图标回退被拦截时的警告（每次会话只警告一次） */
function warnOnlineIconOnce(icon: string): void {
  if (onlineIconWarned) return;
  onlineIconWarned = true;
  console.warn(
    `[ReIcon] 生产环境默认不请求在线图标（api.iconify.design）。` +
      `图标 "${icon}" 未在离线注册表（offlineIconNames.ts）中，已渲染空占位。` +
      `如需在线回退请设置 VITE_ICON_ONLINE_FALLBACK=true，` +
      `或把该图标补进 offlineIcon.ts。`
  );
}

/**
 * 支持 `iconfont`、`SVG` 字符串、`SVG` 函数组件、图片 `URL` 以及 `iconify` 中所有的图标
 * @see 点击查看文档图标篇 {@link https://pure-admin.cn/pages/icon/}
 * @param icon 必传 图标
 * @param attrs 可选 iconType 属性
 * @returns Component
 */
export function useRenderIcon(icon: any, attrs?: iconType): Component {
  if (typeof icon === "string" && svgReg.test(icon)) {
    // SVG 字符串
    let cleanedSvg = svgCache.get(icon);
    if (cleanedSvg === undefined) {
      if (svgCache.size > 200) svgCache.clear();
      cleanedSvg = icon.replace(
        /<svg([^>]*)>/,
        (_, a) => `<svg${a.replace(/\s*(width|height)="[^"]*"/g, "")}>`
      );
      svgCache.set(icon, cleanedSvg);
    }
    return defineComponent({
      name: "SvgRawIcon",
      render: () =>
        h("span", {
          class: "svg-raw-icon",
          innerHTML: cleanedSvg,
          ...attrs
        })
    });
  } else if (typeof icon === "string" && imgReg.test(icon)) {
    // 图片 URL
    return defineComponent({
      name: "ImgIcon",
      render: () =>
        h("img", {
          src: icon,
          style: {
            width: "18px",
            height: "18px",
            minWidth: "18px",
            objectFit: "contain"
          },
          ...attrs
        })
    });
  } else if (ifReg.test(icon)) {
    // iconfont
    const name = icon.split(ifReg)[1];
    const spaceIdx = name.indexOf(" ");
    const iconName = spaceIdx === -1 ? name : name.slice(0, spaceIdx);
    const iconType = spaceIdx === -1 ? name : name.slice(spaceIdx + 1);
    return defineComponent({
      name: "FontIcon",
      render() {
        return h(FontIcon, {
          icon: iconName,
          iconType,
          ...attrs
        });
      }
    });
  } else if (typeof icon === "function" || typeof icon?.render === "function") {
    // SVG 函数组件
    return attrs ? h(icon, { ...attrs }) : icon;
  } else if (typeof icon === "object") {
    return defineComponent({
      name: "OfflineIcon",
      render() {
        return h(IconifyIconOffline, {
          icon: icon,
          ...attrs
        });
      }
    });
  } else {
    /*
     * 字符串图标名（如 `ri:settings-3-line` / `ep:menu`）。
     *
     * 原逻辑：含 ":" 就用在线组件。但后端菜单图标恰好都是冒号格式，
     * 于是每次渲染菜单都会去 api.iconify.design 拉数据——弱网/内网下首屏
     * 被拖到 20s+，甚至请求挂起。
     *
     * 现逻辑：先把 ":" 归一成 "/"（本地注册的命名形式），若该名字已在
     * offlineIconNames 中注册就用离线组件；未注册时区分环境：
     * - dev 环境保留在线回退（IconifyIconOnline），方便管理员在图标
     *   选择器里试到未预置的图标；
     * - 生产构建默认不走在线请求（渲染空占位 + 警告一次），避免线上
     *   依赖 api.iconify.design；可用 VITE_ICON_ONLINE_FALLBACK=true
     *   强制开启在线回退。
     *
     * 注意区分两条路径：`~icons/xxx`（UnpluginIcons，offlineIcon.ts 里的
     * 静态导入）属于本地离线注册，不是在线回退；只有 IconifyIconOnline
     * （@iconify/vue 运行时请求）才是本处要按环境拦截的在线路径。
     */
    return defineComponent({
      name: "Icon",
      render() {
        if (!icon) return;
        const offlineName = String(icon).replace(":", "/");
        const useOffline =
          !String(icon).includes(":") ||
          OFFLINE_ICON_NAMES.includes(offlineName);
        if (!useOffline && !allowOnlineFallback) {
          // 生产环境且未开启强制开关：渲染空占位（保持菜单图标位的布局），
          // 只在首次命中时警告一次，避免刷屏
          warnOnlineIconOnce(String(icon));
          return h("span", {
            class: "icon-offline-missing-placeholder",
            style: {
              display: "inline-block",
              width: `${attrs?.width ?? 18}px`,
              height: `${attrs?.height ?? 18}px`
            }
          });
        }
        return h(useOffline ? IconifyIconOffline : IconifyIconOnline, {
          icon: useOffline ? offlineName : icon,
          ...attrs
        });
      }
    });
  }
}
