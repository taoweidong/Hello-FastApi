import { request } from '@umijs/max';
import { message, notification } from 'antd';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { errorConfig } from './requestErrorConfig';

vi.mock('antd', () => ({
  message: {
    warning: vi.fn(),
    error: vi.fn(),
  },
  notification: {
    open: vi.fn(),
  },
}));

vi.mock('@umijs/max', () => ({
  getIntl: vi.fn(() => ({
    formatMessage: vi.fn(({ defaultMessage }) => defaultMessage),
  })),
  // 401 续期重放路径使用
  request: vi.fn(),
}));

describe('requestErrorConfig', () => {
  // biome-ignore lint/style/noNonNullAssertion: config handlers are always defined
  const errorThrower = errorConfig.errorConfig!.errorThrower!;
  // biome-ignore lint/style/noNonNullAssertion: config handlers are always defined
  const errorHandler = errorConfig.errorConfig!.errorHandler!;
  // 401 续期重放逻辑位于响应拦截器的 rejection 处理器（tuple 第二项）
  const responseRejection = (
    errorConfig.responseInterceptors as Array<
      [(response: unknown) => unknown, (error: unknown) => Promise<unknown>]
    >
  )[0][1];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('errorThrower', () => {
    it('should throw error when success is false', () => {
      const response = {
        success: false,
        data: null,
        errorCode: 400,
        errorMessage: 'Bad Request',
        showType: 2,
      };

      expect(() => {
        errorThrower(response);
      }).toThrow('Bad Request');
    });

    it('should not throw error when success is true', () => {
      const response = {
        success: true,
        data: { id: 1 },
      };

      expect(() => {
        errorThrower(response);
      }).not.toThrow();
    });

    it('should throw BizError with correct info', () => {
      const response = {
        success: false,
        data: { detail: 'more info' },
        errorCode: 403,
        errorMessage: 'Forbidden',
        showType: 3,
      };

      expect.assertions(5);
      try {
        errorThrower(response);
      } catch (error: any) {
        expect(error.name).toBe('BizError');
        expect(error.info.errorCode).toBe(403);
        expect(error.info.errorMessage).toBe('Forbidden');
        expect(error.info.showType).toBe(3);
        expect(error.info.data).toEqual({ detail: 'more info' });
      }
    });
  });

  describe('errorHandler', () => {
    it('should rethrow error when skipErrorHandler is true', async () => {
      const error = new Error('Test error');
      const opts = { skipErrorHandler: true };

      // errorHandler 为 async：skipErrorHandler 时以 Promise rejection 透传
      await expect(errorHandler(error, opts)).rejects.toThrow('Test error');
    });

    it('should handle SILENT showType', () => {
      const error: any = new Error('Silent error');
      error.name = 'BizError';
      error.info = {
        errorCode: 1001,
        errorMessage: 'Silent error',
        showType: 0,
      };

      errorHandler(error, {});

      expect(message.warning).not.toHaveBeenCalled();
      expect(message.error).not.toHaveBeenCalled();
      expect(notification.open).not.toHaveBeenCalled();
    });

    it('should handle WARN_MESSAGE showType', () => {
      const error: any = new Error('Warning');
      error.name = 'BizError';
      error.info = {
        errorCode: 1002,
        errorMessage: 'This is a warning',
        showType: 1,
      };

      errorHandler(error, {});

      expect(message.warning).toHaveBeenCalledWith('This is a warning');
    });

    it('should handle ERROR_MESSAGE showType', () => {
      const error: any = new Error('Error message');
      error.name = 'BizError';
      error.info = {
        errorCode: 1003,
        errorMessage: 'This is an error',
        showType: 2,
      };

      errorHandler(error, {});

      expect(message.error).toHaveBeenCalledWith('This is an error');
    });

    it('should handle NOTIFICATION showType', () => {
      const error: any = new Error('Notification');
      error.name = 'BizError';
      error.info = {
        errorCode: 1004,
        errorMessage: 'This is a notification',
        showType: 3,
      };

      errorHandler(error, {});

      expect(notification.open).toHaveBeenCalledWith({
        title: 1004,
        description: 'This is a notification',
      });
    });

    it('should handle REDIRECT showType', () => {
      const error: any = new Error('Redirect');
      error.name = 'BizError';
      error.info = {
        errorCode: 401,
        errorMessage: 'Unauthorized',
        showType: 9,
      };

      errorHandler(error, {});
      // REDIRECT 分支当前不执行导航，也不应触发任何消息/通知提示
      expect(message.warning).not.toHaveBeenCalled();
      expect(message.error).not.toHaveBeenCalled();
      expect(notification.open).not.toHaveBeenCalled();
    });

    it('should handle default case for unknown showType', () => {
      const error: any = new Error('Unknown type');
      error.name = 'BizError';
      error.info = {
        errorCode: 1005,
        errorMessage: 'Unknown error type',
        showType: 99,
      };

      errorHandler(error, {});

      expect(message.error).toHaveBeenCalledWith('Unknown error type');
    });

    it('should handle axios response error', () => {
      const error: any = new Error('Axios error');
      error.response = {
        status: 500,
        data: {},
      };

      errorHandler(error, {});

      expect(message.error).toHaveBeenCalledWith('Response status:500');
    });

    it('should refresh token and retry once on 401', async () => {
      localStorage.setItem(
        'react-admin-auth',
        JSON.stringify({
          state: { accessToken: 'old', refreshToken: 'r1', username: 'admin' },
        }),
      );
      vi.mocked(request).mockResolvedValueOnce({
        code: 0,
        data: {
          accessToken: 'new-a',
          refreshToken: 'r2',
          expires: '2026-01-01T00:00:00+00:00',
        },
      });
      vi.mocked(request).mockResolvedValueOnce({ code: 0, data: {} });

      const error: any = new Error('Unauthorized');
      // axios 错误对象：请求配置同时挂在 error.config 与 error.response.config
      error.config = { url: '/api/system/mine', method: 'GET' };
      error.response = {
        status: 401,
        config: { url: '/api/system/mine', method: 'GET' },
      };

      // 重放逻辑在响应拦截器 rejection 处理器中：成功续期 → 返回重放响应
      const ret = await responseRejection(error);

      expect(request).toHaveBeenCalledWith(
        '/api/system/refresh-token',
        expect.objectContaining({ method: 'POST' }),
      );
      expect(request).toHaveBeenCalledWith(
        '/api/system/mine',
        expect.objectContaining({ method: 'GET', __isRetry: true }),
      );
      expect(ret).toEqual({ code: 0, data: {} });
      // 新令牌写回本地登录态
      const stored = JSON.parse(
        localStorage.getItem('react-admin-auth') as string,
      );
      expect(stored.state.accessToken).toBe('new-a');
      expect(stored.state.refreshToken).toBe('r2');
    });

    it('should not refresh for whitelisted 401 (login/refresh/logout)', async () => {
      const error: any = new Error('Unauthorized');
      error.config = { url: '/api/system/login', method: 'POST' };
      error.response = {
        status: 401,
        config: { url: '/api/system/login', method: 'POST' },
      };

      await expect(responseRejection(error)).rejects.toThrow('Unauthorized');

      expect(request).not.toHaveBeenCalled();
      expect(message.warning).not.toHaveBeenCalled();
    });

    it('should logout when refresh fails on 401', async () => {
      localStorage.setItem(
        'react-admin-auth',
        JSON.stringify({
          state: { accessToken: 'old', refreshToken: 'r-bad' },
        }),
      );
      vi.mocked(request).mockRejectedValueOnce(
        new Error('invalid refresh token'),
      );

      const error: any = new Error('Unauthorized');
      // axios 错误对象：请求配置同时挂在 error.config 与 error.response.config
      error.config = { url: '/api/system/mine', method: 'GET' };
      error.response = {
        status: 401,
        config: { url: '/api/system/mine', method: 'GET' },
      };

      await expect(responseRejection(error)).rejects.toThrow('Unauthorized');

      expect(request).toHaveBeenCalledTimes(1);
      expect(message.warning).toHaveBeenCalledWith('登录已过期，请重新登录');
      expect(localStorage.getItem('react-admin-auth')).toBeNull();
    });

    it('should handle offline error', () => {
      const error: any = new Error('Network error');
      error.request = {};

      const originalOnLine = Object.getOwnPropertyDescriptor(
        navigator,
        'onLine',
      );
      Object.defineProperty(navigator, 'onLine', {
        configurable: true,
        writable: true,
        value: false,
      });

      try {
        errorHandler(error, {});

        expect(message.error).toHaveBeenCalledWith(
          'Network unavailable. Please check your connection and try again.',
        );
      } finally {
        if (originalOnLine) {
          Object.defineProperty(navigator, 'onLine', originalOnLine);
        } else {
          delete (navigator as { onLine?: boolean }).onLine;
        }
      }
    });

    it('should handle request error with no response', () => {
      const error: any = new Error('Request error');
      error.request = {};

      errorHandler(error, {});

      expect(message.error).toHaveBeenCalledWith(
        'None response! Please retry.',
      );
    });

    it('should handle generic error', () => {
      const error: any = new Error('Generic error');

      errorHandler(error, {});

      expect(message.error).toHaveBeenCalledWith(
        'Request error, please retry.',
      );
    });
  });

  describe('requestInterceptors', () => {
    // The interceptor is registered as a plain function (not a tuple),
    // so narrow the union type to a callable for the test. It is async and
    // injects the Authorization header from the stored login state.
    const interceptor = errorConfig.requestInterceptors?.[0] as (config: {
      headers?: Record<string, unknown>;
      url?: string;
      method?: string;
    }) => Promise<{ headers?: Record<string, unknown>; url?: string }>;

    it('should pass through config without modification when no token stored', async () => {
      const config = {
        url: 'https://api.example.com/users',
        method: 'GET',
      };

      const result = await interceptor(config);

      // 令牌注入依赖 localStorage，测试环境（node）未存储登录态时原样透传
      expect(result.url).toBe('https://api.example.com/users');
    });

    it('should attach Authorization header from stored login state', async () => {
      vi.stubGlobal('localStorage', {
        getItem: (key: string) =>
          key === 'react-admin-auth'
            ? JSON.stringify({ state: { accessToken: 'token-abc' } })
            : null,
        setItem: vi.fn(),
        removeItem: vi.fn(),
      });
      try {
        const result = await interceptor({
          url: 'https://api.example.com/users',
          method: 'GET',
          headers: {},
        });

        expect(result.headers).toEqual({ Authorization: 'Bearer token-abc' });
        expect(result.url).toBe('https://api.example.com/users');
      } finally {
        vi.unstubAllGlobals();
      }
    });

    it('should handle URL without config', async () => {
      const config = {};

      const result = await interceptor(config);

      expect(result.url).toBeUndefined();
    });
  });
});
