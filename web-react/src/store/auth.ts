import { create } from "zustand";
import { persist } from "zustand/middleware";

/** 登录响应（与后端 LoginResponse 对齐） */
export interface LoginResult {
  accessToken: string;
  refreshToken: string;
  expires: string;
  roles: string[];
  permissions: string[];
  username: string;
  nickname: string;
  avatar: string;
}

export interface AuthState {
  accessToken: string;
  refreshToken: string;
  username: string;
  nickname: string;
  avatar: string;
  roles: string[];
  /** 按钮级权限码（登录响应的 permissions） */
  permissions: string[];
  setLogin: (data: LoginResult) => void;
  /** 刷新轮换后更新令牌对 */
  setTokens: (accessToken: string, refreshToken: string) => void;
  clear: () => void;
}

/**
 * 令牌与用户信息持久化（localStorage）。
 * 与 Vue 版差异：Vue 版放 Cookie（authorized-token）+ localStorage 混合；
 * React 版统一 localStorage，由 axios 拦截器注入 Bearer 头。
 */
export const useAuthStore = create<AuthState>()(
  persist(
    set => ({
      accessToken: "",
      refreshToken: "",
      username: "",
      nickname: "",
      avatar: "",
      roles: [],
      permissions: [],
      setLogin: data =>
        set({
          accessToken: data.accessToken,
          refreshToken: data.refreshToken,
          username: data.username,
          nickname: data.nickname,
          avatar: data.avatar,
          roles: data.roles,
          permissions: data.permissions
        }),
      setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
      clear: () =>
        set({
          accessToken: "",
          refreshToken: "",
          username: "",
          nickname: "",
          avatar: "",
          roles: [],
          permissions: []
        })
    }),
    { name: "react-admin-auth" }
  )
);
