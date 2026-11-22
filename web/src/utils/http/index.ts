import Axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type CustomParamsSerializer
} from "axios";
import type {
  PureHttpError,
  RequestMethods,
  PureHttpResponse,
  PureHttpRequestConfig
} from "./types.d";
import { stringify } from "qs";
import { message } from "@/utils/message";
import { $t, transformI18n } from "@/plugins/i18n";
import { getToken, formatToken } from "@/utils/auth";
import { useUserStoreHook } from "@/store/modules/user";

// 相关配置请参考：www.axios-js.com/zh-cn/docs/#axios-request-config-1
const defaultConfig: AxiosRequestConfig = {
  // API 基础路径，所有请求会自动添加此前缀
  baseURL: "/api/system",
  // 请求超时时间
  timeout: 10000,
  headers: {
    Accept: "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest"
  },
  // 数组格式参数序列化（https://github.com/axios/axios/issues/5142）
  paramsSerializer: {
    serialize: stringify as unknown as CustomParamsSerializer
  }
};

class PureHttp {
  constructor() {
    this.httpInterceptorsRequest();
    this.httpInterceptorsResponse();
  }

  /**
   * `token`过期后，暂存待执行的请求。
   * `resolve`：刷新成功后携带新 token 重放；`reject`：刷新失败后逐一拒绝，
   * 避免挂起请求被静默丢弃而永远 pending。
   */
  private static requests: {
    resolve: (token: string) => void;
    reject: (reason?: unknown) => void;
  }[] = [];

  /** 防止重复刷新`token` */
  private static isRefreshing = false;

  /** 并发401单飞锁：登出流程进行中时（promise 未 settle），后续 401 跳过提示与登出 */
  private static loggingOutPromise: Promise<void> | null = null;

  /** 初始化配置对象 */
  private static initConfig: PureHttpRequestConfig = {};

  /** 保存当前`Axios`实例对象 */
  private static axiosInstance: AxiosInstance = Axios.create(defaultConfig);

  /** 重连原始请求：把挂起请求的 resolve/reject 入队，由 token 刷新结果决定重放或拒绝 */
  private static retryOriginalRequest(config: PureHttpRequestConfig) {
    return new Promise<PureHttpRequestConfig>((resolve, reject) => {
      PureHttp.requests.push({
        resolve: token => {
          config.headers["Authorization"] = formatToken(token);
          resolve(config);
        },
        reject
      });
    });
  }

  /** 请求拦截 */
  private httpInterceptorsRequest(): void {
    PureHttp.axiosInstance.interceptors.request.use(
      async (config: PureHttpRequestConfig): Promise<any> => {
        // 优先判断post/get等方法是否传入回调，否则执行初始化设置等回调
        if (typeof config.beforeRequestCallback === "function") {
          config.beforeRequestCallback(config);
          return config;
        }
        if (PureHttp.initConfig.beforeRequestCallback) {
          PureHttp.initConfig.beforeRequestCallback(config);
          return config;
        }
        /** 请求白名单，放置一些不需要`token`的接口（通过设置请求白名单，防止`token`过期后再请求造成的死循环问题） */
        const whiteList = ["/refresh-token", "/login"];
        return whiteList.some(url => config.url.endsWith(url))
          ? config
          : new Promise(resolve => {
              const data = getToken();
              if (data) {
                const now = new Date().getTime();
                const expired = parseInt(data.expires) - now <= 0;
                if (expired) {
                  if (!PureHttp.isRefreshing) {
                    PureHttp.isRefreshing = true;
                    // token过期刷新
                    useUserStoreHook()
                      .handRefreshToken({ refreshToken: data.refreshToken })
                      .then(res => {
                        const token = res.data.accessToken;
                        config.headers["Authorization"] = formatToken(token);
                        // 刷新成功：携带新 token 重放挂起请求后清空队列
                        PureHttp.requests.forEach(({ resolve }) =>
                          resolve(token)
                        );
                        PureHttp.requests = [];
                      })
                      .catch(err => {
                        /*
                         * 刷新失败：逐个拒绝挂起请求（带刷新失败错误）后再清空队列。
                         * 此前直接 `requests = []` 会把挂起请求静默丢弃，
                         * 调用方拿不到任何结果而永远 pending。
                         */
                        PureHttp.requests.forEach(({ reject }) => reject(err));
                        PureHttp.requests = [];
                        useUserStoreHook().logOut();
                        message(transformI18n($t("login.pureLoginExpired")), {
                          type: "warning"
                        });
                      })
                      .finally(() => {
                        PureHttp.isRefreshing = false;
                      });
                  }
                  resolve(PureHttp.retryOriginalRequest(config));
                } else {
                  config.headers["Authorization"] = formatToken(
                    data.accessToken
                  );
                  resolve(config);
                }
              } else {
                resolve(config);
              }
            });
      },
      error => {
        return Promise.reject(error);
      }
    );
  }

  /** 响应拦截 */
  private httpInterceptorsResponse(): void {
    const instance = PureHttp.axiosInstance;
    instance.interceptors.response.use(
      (response: PureHttpResponse) => {
        const $config = response.config;
        // 优先判断post/get等方法是否传入回调，否则执行初始化设置等回调
        if (typeof $config.beforeResponseCallback === "function") {
          $config.beforeResponseCallback(response);
          return response.data;
        }
        if (PureHttp.initConfig.beforeResponseCallback) {
          PureHttp.initConfig.beforeResponseCallback(response);
          return response.data;
        }
        return response.data;
      },
      (error: PureHttpError) => {
        const $error = error;
        $error.isCancelRequest = Axios.isCancel($error);

        // 处理401未授权：token失效时强制登出并跳转登录页
        const status = error.response?.status;
        if (status === 401) {
          // 登录/登出/刷新token请求白名单：登出流程自身可能携带失效令牌，
          // 若其 401 再次触发登出会形成请求循环
          const whiteList = ["/refresh-token", "/login", "/logout"];
          const url = error.config?.url || "";
          if (
            !whiteList.some(w => url.endsWith(w)) &&
            !PureHttp.loggingOutPromise
          ) {
            message(transformI18n($t("login.pureLoginExpired")), {
              type: "warning"
            });
            /*
             * Promise 单飞锁：此前 isLoggingOut 同步置位后又同步复位，
             * 并发的 401 仍会重复弹窗、重复登出。改为持有 logOut 的 promise，
             * 流程 settle 后才复位；期间后续 401 直接跳过提示与登出。
             * catch 兜底保证 logOut 失败时锁也能释放，不会永久阻塞后续流程。
             */
            PureHttp.loggingOutPromise = Promise.resolve(
              useUserStoreHook().logOut()
            )
              .catch(() => undefined)
              .finally(() => {
                PureHttp.loggingOutPromise = null;
              });
          }
        } else if (!$error.isCancelRequest) {
          /*
           * 服务端错误（5xx）与网络中断此前被静默吞掉：表格只剩一片空白，
           * 用户无从判断是"真的没有数据"还是"加载失败"。这里补一条全局提示。
           *
           * 只覆盖 5xx / 无响应（断网、超时、后端崩溃）；
           * 4xx 属业务校验结果，由各页面自行在表单或消息里呈现，避免重复打扰。
           */
          if (status === undefined || status >= 500) {
            message(
              status === undefined
                ? "网络连接失败，请检查网络后重试"
                : "服务暂时不可用，请稍后重试",
              { type: "error" }
            );
          }
        }

        // 所有的响应异常 区分来源为取消请求/非取消请求
        return Promise.reject($error);
      }
    );
  }

  /** 通用请求工具函数 */
  public request<T>(
    method: RequestMethods,
    url: string,
    param?: AxiosRequestConfig,
    axiosConfig?: PureHttpRequestConfig
  ): Promise<T> {
    const config = {
      method,
      url,
      ...param,
      ...axiosConfig
    } as PureHttpRequestConfig;

    // 单独处理自定义请求/响应回调
    return new Promise((resolve, reject) => {
      PureHttp.axiosInstance
        .request(config)
        .then((response: undefined) => {
          resolve(response);
        })
        .catch(error => {
          reject(error);
        });
    });
  }

  /** 单独抽离的`post`工具函数 */
  public post<T, P>(
    url: string,
    params?: AxiosRequestConfig<P>,
    config?: PureHttpRequestConfig
  ): Promise<T> {
    return this.request<T>("post", url, params, config);
  }

  /** 单独抽离的`get`工具函数 */
  public get<T, P>(
    url: string,
    params?: AxiosRequestConfig<P>,
    config?: PureHttpRequestConfig
  ): Promise<T> {
    return this.request<T>("get", url, params, config);
  }
}

export const http = new PureHttp();
