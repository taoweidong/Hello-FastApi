import { createBrowserRouter, createRoutesFromElements, Navigate, Route } from "react-router-dom";
import { AdminLayout } from "@/layout/AdminLayout";
import { PageForPath } from "@/pages/pageMap";
import LoginPage from "@/pages/login";
import { RequireAuth, RedirectIfAuthed } from "@/auth/guards";

// 路由表：登录页独立；业务页面统一在 AdminLayout 下，
// 具体页面由 PageForPath 按后端动态菜单 path 渲染（React.lazy 懒加载）；
// 菜单/权限由后端 /get-async-routes 动态驱动（与 Vue 版同一端点）。
export const router = createBrowserRouter(
  createRoutesFromElements(
    <>
      <Route element={<RedirectIfAuthed />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route element={<RequireAuth />}>
        <Route element={<AdminLayout />}>
          <Route path="/welcome" element={<PageForPath />} />
          <Route path="/system/user" element={<PageForPath />} />
          <Route path="*" element={<PageForPath />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </>
  ),
  { basename: "/" }
);
