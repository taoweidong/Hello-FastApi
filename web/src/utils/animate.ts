/**
 * animate.css 按需加载工具（2025 资源瘦身批次）。
 *
 * 背景：原先 `src/layout/index.vue` 顶层 `import "animate.css"`，全量 CSS
 * （约 80KB）常驻首屏，而实际只有两类场景用到它：
 *  1. 路由 meta 声明了 `enterTransition/leaveTransition`（lay-content 的
 *     transitionMain 会给 Transition 挂 `animate__animated` 类名）；
 *  2. 设置面板的 ReAnimateSelector 悬停预览动画。
 *
 * 现改为：上述场景触发时才动态 `import("animate.css")`，未触发的会话
 * （绝大多数页面不配路由动画）永不加载。模块级 once 标志保证只加载一次，
 * 多处调用共享同一个 Promise，天然防重复。
 */
let loadOnce: Promise<unknown> | null = null;

/** 动态加载 animate.css；多次调用共享同一次加载，未调用则永不加载 */
export function loadAnimateCss(): Promise<unknown> {
  loadOnce ??= import("animate.css");
  return loadOnce;
}
