import axios, { AxiosError, type AxiosRequestConfig } from "axios";
import { App } from "antd";
import { useAuthStore } from "@/store/auth";

export const http = axios.create({
  baseURL: "/api/system",
  timeout: 15000
});

// 统一后端响应封装 { code, message, data }（code===0 成功）
export interface ApiEnvelope<T = unknown> {
  code: number;
  message: string;
  data: T;
}

export function isOk(code: number | undefined): boolean {
  return code === 0;
}

let messageApi: ReturnType<typeof App.useApp>["message"] | null = null;
/** 在 App 上下文中注入 message 实例（antd 静态方法与主题上下文冲突，须用 hook） */
export function bindMessage(api: ReturnType<typeof App.useApp>["message"]): void {
  messageApi = api;
}

function notifyError(text: string): void {
  messageApi?.error(text);
}

// ---- 请求拦截：注入 Bearer（login/refresh 除外） ----
http.interceptors.request.use(config => {
  const url = config.url ?? "";
  const anonymous = url.endsWith("/login") || url.endsWith("/refresh-token");
  if (!anonymous) {
    const { accessToken } = useAuthStore.getState();
    if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

// ---- 401 无感刷新：单飞 + 请求队列（与 Vue 版语义一致） ----
let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const { refreshToken, setTokens, clear } = useAuthStore.getState();
  if (!refreshToken) return false;
  try {
    // 直接用裸 axios，避免拦截器递归
    const res = await axios.post<ApiEnvelope<{ accessToken: string; refreshToken: string }>>(
      "/api/system/refresh-token",
      { refreshToken }
    );
    const { code, data } = res.data;
    if (code !== 0 || !data?.accessToken) return false;
    setTokens(data.accessToken, data.refreshToken);
    return true;
  } catch {
    clear();
    window.location.hash = "#/login";
    return false;
  }
}

http.interceptors.response.use(
  res => {
    const body = res.data as ApiEnvelope;
    // 后端业务码非 0 统一提示（401 走 HTTP 分支，不在此列）
    if (body && typeof body.code === "number" && body.code !== 0 && body.code >= 400) {
      notifyError(body.message || "请求失败");
      return Promise.reject(new axios.AxiosError(body.message, String(body.code), res.config, res.request, res));
    }
    return res;
  },
  async (error: AxiosError<ApiEnvelope>) => {
    const config = error.config as (AxiosRequestConfig & { _retried?: boolean }) | undefined;
    const status = error.response?.status;
    const url = config?.url ?? "";

    if (status === 401 && config && !config._retried && !url.endsWith("/login")) {
      config._retried = true;
      refreshing = refreshing ?? refreshTokens().finally(() => {
        refreshing = null;
      });
      const ok = await refreshing;
      if (ok) return http.request(config);
      notifyError("登录已过期，请重新登录");
      return Promise.reject(error);
    }

    if (status && status >= 500) {
      notifyError("服务暂时不可用，请稍后重试");
    } else if (status === 403) {
      notifyError("没有操作权限");
    } else if (status === 422) {
      // DTO 校验失败：FastAPI detail 数组 → 提示第一条
      const detail = (error.response?.data as { detail?: Array<{ msg?: string }> })?.detail;
      notifyError(detail?.[0]?.msg ? `参数错误：${detail[0].msg}` : "参数校验失败");
    } else if (status === 400) {
      // 业务错误（BusinessError）：后端 message 直接可读
      notifyError(error.response?.data?.message || "请求失败");
    }
    return Promise.reject(error);
  }
);

/** 请求封装：解包 { code, message, data }，失败时抛出（错误提示已统一处理） */
export async function request<T>(config: AxiosRequestConfig): Promise<T> {
  const res = await http.request<ApiEnvelope<T>>(config);
  const body = res.data;
  if (typeof body?.code === "number" && body.code !== 0) {
    throw new Error(body.message || "请求失败");
  }
  return body.data as T;
}
