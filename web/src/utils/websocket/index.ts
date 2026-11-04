import { getToken } from "@/utils/auth";

/**
 * 实时消息 WebSocket 客户端（单例）。
 *
 * - 登录后调用 start() 自动连接；登出调用 stop() 主动断开。
 * - 鉴权：查询参数 ?token=<accessToken>，与 HTTP 共用 JWT。
 * - 心跳：每 25s 发送 {type:"ping"}，服务端回 {type:"pong"}。
 * - 断线重连：指数退避（1s→2s→...→15s），主动 stop() 不重连。
 * - 事件总线：on/off 订阅，服务端消息按 type 派发。
 */

type Listener = (payload: any) => void;

export class RealtimeClient {
  private ws: WebSocket | null = null;
  private heartbeatTimer: number | null = null;
  private reconnectTimer: number | null = null;
  private intentionalClose = false;
  private reconnectDelay = 1000;
  private readonly maxDelay = 15000;
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

    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/api/system/ws?token=${encodeURIComponent(token)}`;

    this.intentionalClose = false;
    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = 1000;
      this.startHeartbeat();
    };
    this.ws.onmessage = evt => {
      try {
        const msg = JSON.parse(evt.data as string);
        if (msg && msg.type) {
          this.emit(msg.type, msg.data ?? msg);
        }
      } catch {
        /* 忽略非法消息 */
      }
    };
    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (!this.intentionalClose) this.scheduleReconnect();
    };
    this.ws.onerror = () => {
      // 随后会触发 onclose，统一在 onclose 处理重连
      this.ws?.close();
    };
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeatTimer = window.setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 25000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.start();
    }, this.reconnectDelay);
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
