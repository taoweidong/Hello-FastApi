import { useEffect } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/store/auth";

/** 登录守卫：无令牌重定向登录页 */
export function RequireAuth(): React.ReactNode {
  const accessToken = useAuthStore(s => s.accessToken);
  const location = useLocation();
  if (!accessToken) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
}

/** 已登录访问 /login 时重定向首页 */
export function RedirectIfAuthed(): React.ReactNode {
  const accessToken = useAuthStore(s => s.accessToken);
  const location = useLocation();
  if (accessToken && location.pathname === "/login") {
    return <Navigate to="/welcome" replace />;
  }
  return <Outlet />;
}
