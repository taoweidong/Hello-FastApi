// 请求配置：错误统一处理 + 拦截器（baseURL 不设置——services/api.ts 已用全路径 /api/system/*）
import type { RequestConfig } from '@umijs/max';
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
  response?: { status: number };
  request?: unknown;
  info?: ResponseStructure;
}

/** 请求拦截器入参（与 umi IRequestOptions 的宽松索引签名保持一致，headers 走索引访问） */
interface InterceptorConfig {
  [key: string]: any;
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
    errorHandler(error, opts) {
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
      } else if (extra.response) {
        // 服务端返回了 2xx 之外的状态码
        const status = extra.response.status;
        if (status === 401) {
          message.error('登录已过期，请重新登录');
        } else {
          message.error(`Response status:${status}`);
        }
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
        const raw = localStorage.getItem('react-admin-auth');
        const accessToken = raw
          ? (JSON.parse(raw)?.state?.accessToken as string | undefined)
          : undefined;
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

  responseInterceptors: [],
};
