import { lazy } from "react";
import { Result } from "antd";
import { useLocation } from "react-router-dom";

/**
 * 页面映射：后端动态菜单 path → React 页面组件。
 * Vue 版的 component 字段（如 system/user/index）在此按 path 映射为 React 实现；
 * 尚未迁移的菜单渲染"建设中"占位（菜单与权限行为保持后端驱动）。
 */
const Welcome = lazy(() => import("@/pages/welcome"));
const UserPage = lazy(() => import("@/pages/system/user"));

export const PAGES: Record<string, React.ReactNode> = {
  "/welcome": <Welcome />,
  "/system/user": <UserPage />
};

/** 未迁移页面的占位 */
export function Placeholder({ title }: { title?: string }): React.ReactNode {
  return (
    <Result
      status="info"
      title={title ?? "建设中"}
      subTitle="该页面正在从 Vue 版迁移到 React 版，可先使用 Vue 版（/）。"
    />
  );
}

/** 按当前路径渲染映射页面；无映射时渲染占位 */
export function PageForPath(): React.ReactNode {
  const location = useLocation();
  return PAGES[location.pathname] ?? <Placeholder />;
}
