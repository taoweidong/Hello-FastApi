// 请求配置：错误统一处理 + 拦截器（baseURL 不设置——services/api.ts 已用全路径 /api/system/*）
import type { RequestConfig } from '@umijs/max';
import { request } from '@umijs/max';
import { message, notification } from 'antd';

/** 异常展示方案 */
enum ErrorShowType {
  SILENT = 0,
  WARN_MESSAGE = 1,
  ERROR_MESSAGE = 2,
  NOTIFICATION = 3,
  REDIRECT = 9,
}

/** errorThrower 依据的业务响应结构（success=false 时抛 BizError） */
interface ResponseStructure {
  success?: boolean;
  data?: unknown;
  errorCode?: number | string;
  errorMessage?: string;
  showType?: ErrorShowType;
}

/** 统一错误处理器需要的附加字段（RequestError = AxiosError | Error） */
interface ErrorExtra {
  response?: {
    status: number;
    config?: {
      url?: string;
      method?: string;
      data?: unknown;
      headers?: Record<string, string>;
      params?: unknown;
    };
  };
  request?: unknown;
  info?: ResponseStructure;
}

/** 请求拦截器入参（与 umi IRequestOptions 的宽松索引签名保持一致，headers 走索引访问） */
interface InterceptorConfig {
  [key: string]: any;
}

/** 本地登录态（shape 由 user/login 页写入） */
interface StoredAuth {
  accessToken: string;
  refreshToken: string;
  expires?: string;
  username?: string;
  nickname?: string;
  avatar?: string;
  permissions?: string[];
}

/** 刷新接口白名单：这些请求 401 时不做续期重试（避免自递归） */
const REFRESH_WHITELIST = ['/login', '/refresh-token', '/logout'];

let refreshPromise: Promise<boolean> | null = null;
let isLoggingOut = false;

function readStoredAuth(): StoredAuth | null {
  try {
    const raw = localStorage.getItem('react-admin-auth');
    return raw ? (JSON.parse(raw)?.state as StoredAuth) : null;
  } catch {
    return null;
  }
}

function writeStoredAuth(state: StoredAuth): void {
  localStorage.setItem('react-admin-auth', JSON.stringify({ state }));
}

/** 登录态失效后的统一登出（提示 + 清存储 + 跳登录页），并发去重 */
function forceLogout(): void {
  if (isLoggingOut) return;
  isLoggingOut = true;
  localStorage.removeItem('react-admin-auth');
  message.warning('登录已过期，请重新登录');
  if (!window.location.pathname.startsWith('/user/login')) {
    window.location.href = '/user/login';
  }
  isLoggingOut = false;
}

/**
 * 单次令牌续期（并发 401 共享同一 Promise）。
 * 旧 refreshToken 单次使用后即被后端拉黑（rotation），成功后写回新令牌对。
 */
async function doRefresh(): Promise<boolean> {
  const stored = readStoredAuth();
  const refreshToken = stored?.refreshToken;
  if (!refreshToken) {
    forceLogout();
    return false;
  }
  try {
    const res = await request<{ code: number; data: StoredAuth }>(
      '/api/system/refresh-token',
      { method: 'POST', data: { refreshToken }, skipErrorHandler: true },
    );
    if (res.code !== 0 || !res.data?.accessToken) {
      forceLogout();
      return false;
    }
    writeStoredAuth({
      ...stored,
      accessToken: res.data.accessToken,
      refreshToken: res.data.refreshToken,
      expires: res.data.expires,
    });
    return true;
  } catch {
    forceLogout();
    return false;
  }
}

function ensureFreshToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null;
    });
  }
  return refreshPromise;
}

export const errorConfig: RequestConfig = {
  errorConfig: {
    /** 抛出器：将 success=false 的响应体转换为 BizError，交由 errorHandler 统一展示 */
    errorThrower(res) {
      const { success, data, errorCode, errorMessage, showType } =
        res as ResponseStructure;
      if (success) {
        return;
      }
      const error = new Error(errorMessage);
      error.name = 'BizError';
      (error as unknown as ErrorExtra).info = {
        errorCode,
        errorMessage,
        showType,
        data,
      };
      throw error;
    },

    /** 统一错误处理器：按 BizError.showType / HTTP 状态 / 网络状态分发提示 */
    async errorHandler(error, opts) {
      if (opts?.skipErrorHandler) throw error;
      const extra = error as ErrorExtra;
      // errorThrower 抛出的业务错误
      if (error.name === 'BizError' && extra.info) {
        const { errorMessage, errorCode, showType } = extra.info;
        switch (showType) {
          case ErrorShowType.SILENT:
            // 静默：不提示
            break;
          case ErrorShowType.WARN_MESSAGE:
            message.warning(errorMessage);
            break;
          case ErrorShowType.ERROR_MESSAGE:
            message.error(errorMessage);
            break;
          case ErrorShowType.NOTIFICATION:
            // 通知场景沿用 errorCode 作为标题
            notification.open({
              title: errorCode,
              description: errorMessage,
            } as never);
            break;
          case ErrorShowType.REDIRECT:
            // TODO: 按业务跳转（如登录页）
            break;
          default:
            message.error(errorMessage);
        }
        return;
      }

      // 401 已在响应拦截器做过一次续期重试：到这里说明续期失败（forceLogout 已提示）或白名单请求
      const status = extra.response?.status;
      if (status === 401) {
        return;
      }

      if (extra.response) {
        message.error(`Response status:${status}`);
      } else if (extra.request) {
        // 请求已发出但未收到响应（浏览器离线时给出明确提示；node 环境无 onLine 定义）
        if (typeof navigator !== 'undefined' && navigator.onLine === false) {
          message.error(
            'Network unavailable. Please check your connection and try again.',
          );
        } else {
          message.error('None response! Please retry.');
        }
      } else {
        // 请求配置阶段触发的错误
        message.error('Request error, please retry.');
      }
    },
  },

  requestInterceptors: [
    // axios 变体拦截器：注入令牌（登录态存于 localStorage 'react-admin-auth'，shape 见 user/login 页）
    async (config: InterceptorConfig) => {
      try {
        const accessToken = readStoredAuth()?.accessToken;
        if (accessToken)
          config.headers = {
            ...(config.headers ?? {}),
            Authorization: `Bearer ${accessToken}`,
          };
      } catch {
        // 令牌解析失败时不注入，由后端 401 兜底
      }
      return config;
    },
  ],

  responseInterceptors: [
    [
      // 成功路径原样透传
      (response) => response,
      // 401：先用 refreshToken 续期一次并重放原请求（axios 拦截器可 resolve 新响应）
      // umi plugin-request 的 errorHandler 返回值会被丢弃（仅展示用），重试必须在响应拦截器完成
      async (axiosError: unknown): Promise<any> => {
        const error = axiosError as {
          response?: { status?: number };
          config?: { url?: string; __isRetry?: boolean } & Record<
            string,
            unknown
          >;
        };
        const status = error.response?.status;
        const url = error.config?.url ?? '';
        if (
          status === 401 &&
          error.config?.url &&
          !error.config.__isRetry &&
          !REFRESH_WHITELIST.some((w) => url.endsWith(w))
        ) {
          const refreshed = await ensureFreshToken();
          if (refreshed) {
            return request(url, {
              ...error.config,
              __isRetry: true,
            } as never);
          }
        }
        throw axiosError as Error;
      },
    ],
  ],
};
