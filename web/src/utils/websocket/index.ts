import { getToken } from "@/utils/auth";

/**
 * 实时消息 WebSocket 客户端（单例）。
 *
 * - 登录后调用 start() 自动连接；登出调用 stop() 主动断开。
 * - 鉴权：首帧鉴权 —— 连接成功后立即发送 {"type":"auth","token":"<accessToken>"}，
 *   服务端在 5s 窗口内校验；token 不再拼入 URL（避免进入代理/网关访问日志）。
 * - 心跳：每 25s 发送 {type:"ping"}，服务端回 {type:"pong"}；收到任何服务端
 *   消息（pong / 业务推送）都刷新 lastPongTime，超过 2×25s 无响应判定为假死
 *   连接，主动 close 走既有重连路径。
 * - 断线重连：指数退避（1s→2s→…→15s）叠加 ±20% 随机抖动，避免多客户端同时
 *   重连造成惊群；主动 stop() 与服务端鉴权失败（1008）不重连 —— 1008 说明
 *   token 已失效，重连只会重复失败，登出/续期由 HTTP 层 401 单飞机制处理。
 * - 事件总线：on/off 订阅，服务端消息按 type 派发。
 */

type Listener = (payload: any) => void;

/** 心跳间隔（与服务端约定 25s） */
const HEARTBEAT_INTERVAL = 25000;
/** 判定连接假死：连续 2 个心跳周期未收到任何服务端消息 */
const DEAD_CONNECTION_FACTOR = 2;
/** 重连退避基数与上限 */
const BASE_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 15000;
/** 重连退避随机抖动幅度（±20%） */
const RECONNECT_JITTER_RATIO = 0.2;
/** 服务端鉴权失败（token 无效/过期/超时未鉴权）的 WebSocket 关闭码 */
const WS_CLOSE_UNAUTHORIZED = 1008;

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private heartbeatTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private intentionalClose = false;
  private reconnectDelay = BASE_RECONNECT_DELAY;
  private readonly maxDelay = MAX_RECONNECT_DELAY;
  /** 最近一次收到服务端消息的时间戳（心跳活性校验基准） */
  private lastPongTime = 0;
  private readonly listeners = new Map<string, Set<Listener>>();

  /** 开始连接（无 token 时静默 no-op）。重复调用幂等。 */
  start(): void {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN ||
        this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    const token = getToken()?.accessToken;
    if (!token) return;

    this.intentionalClose = false;
    const proto = location.protocol === "https:" ? "wss" : "ws";
    // 首帧鉴权：URL 不携带 token，避免 token 出现在代理/网关日志中
    const url = `${proto}://${location.host}/api/system/ws`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = BASE_RECONNECT_DELAY;
      this.lastPongTime = Date.now();
      // 首帧鉴权：必须先于其它任何消息发送，服务端在 5s 窗口内等待该帧
      this.ws?.send(JSON.stringify({ type: "auth", token }));
      this.startHeartbeat();
    };
    this.ws.onmessage = evt => {
      // 任何服务端消息（pong / 业务推送）都视为连接活性
      this.lastPongTime = Date.now();
      try {
        const msg = JSON.parse(evt.data as string);
        if (msg && msg.type) {
          this.emit(msg.type, msg.data ?? msg);
        }
      } catch {
        /* 忽略非法消息 */
      }
    };
    this.ws.onclose = evt => {
      this.stopHeartbeat();
      if (this.intentionalClose) return;
      if (evt?.code === WS_CLOSE_UNAUTHORIZED) {
        // 鉴权失败：token 已失效，重连只会风暴式失败；清理定时器并复位退避，
        // 等待 HTTP 层 401 单飞机制完成登出/续期后再由 start() 重连
        if (this.reconnectTimer !== null) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
        this.reconnectDelay = BASE_RECONNECT_DELAY;
        this.ws = null;
        return;
      }
      this.scheduleReconnect();
    };
    this.ws.onerror = () => {
      // 随后会触发 onclose，统一在 onclose 处理重连
      this.ws?.close();
    };
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState !== WebSocket.OPEN) return;
      // pong 校验：超过 2 个心跳周期未收到任何服务端消息，判定假死连接，
      // 停止心跳并主动 close —— onclose（非 1008/非主动）会走既有重连路径
      if (
        Date.now() - this.lastPongTime >
        HEARTBEAT_INTERVAL * DEAD_CONNECTION_FACTOR
      ) {
        this.stopHeartbeat();
        this.ws.close();
        return;
      }
      this.ws.send(JSON.stringify({ type: "ping" }));
    }, HEARTBEAT_INTERVAL);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  /** 退避延时叠加 ±20% 随机抖动，避免多客户端同相位重连的惊群效应 */
  private nextReconnectDelay(): number {
    const jitter = this.reconnectDelay * RECONNECT_JITTER_RATIO;
    const delay = this.reconnectDelay + (Math.random() * 2 - 1) * jitter;
    return Math.min(Math.round(delay), this.maxDelay);
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.start();
    }, this.nextReconnectDelay());
    this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxDelay);
  }

  /** 主动停止（登出时调用，避免重连风暴）。 */
  stop(): void {
    this.intentionalClose = true;
    this.stopHeartbeat();
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
  }

  /** 订阅某类型消息。 */
  on(event: string, cb: Listener): void {
    if (!this.listeners.has(event)) this.listeners.set(event, new Set());
    this.listeners.get(event)!.add(cb);
  }

  /** 取消订阅。 */
  off(event: string, cb: Listener): void {
    this.listeners.get(event)?.delete(cb);
  }

  private emit(event: string, payload: any): void {
    this.listeners.get(event)?.forEach(cb => {
      try {
        cb(payload);
      } catch {
        /* 监听器异常隔离 */
      }
    });
  }
}

export const realtime = new RealtimeClient();
