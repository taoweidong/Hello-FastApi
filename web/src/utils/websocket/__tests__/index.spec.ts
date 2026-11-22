/**
 * realtime WebSocket 客户端单元测试。
 *
 * 覆盖：幂等 start、无 token no-op、首帧鉴权（URL 不带 token，open 后立即发 auth）、
 * stop 语义（主动关闭不重连）、1008 鉴权失败不重连、心跳 ping + pong 超时主动重连、
 * 指数退避 ±20% jitter、事件总线派发与异常隔离、非法消息静默。
 * 通过替换实例内部的 WebSocket 构造器避免真实网络。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// 拦截 token 来源：start() 依据 getToken().accessToken 决定是否连接
const mockGetToken = vi.fn();
vi.mock("@/utils/auth", () => ({
  getToken: () => mockGetToken()
}));

import { RealtimeClient } from "../index";

const AUTH_FRAME = JSON.stringify({ type: "auth", token: "tok-1" });
const PING_FRAME = JSON.stringify({ type: "ping" });

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;
  static CONNECTING = 0;
  readyState = 0;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((evt: { data: string }) => void) | null = null;
  onclose: ((evt?: { code?: number }) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = 3;
    this.onclose?.();
  }

  /** 测试辅助：模拟连接建立 */
  simulateOpen() {
    this.readyState = 1;
    this.onopen?.();
  }

  /** 测试辅助：模拟服务端消息 */
  simulateMessage(data: unknown) {
    this.onmessage?.({
      data: typeof data === "string" ? data : JSON.stringify(data)
    });
  }
}

describe("RealtimeClient", () => {
  let client: RealtimeClient;
  let OriginalWebSocket: unknown;

  beforeEach(() => {
    vi.useFakeTimers();
    OriginalWebSocket = globalThis.WebSocket;
    (globalThis as any).WebSocket = FakeWebSocket;
    FakeWebSocket.instances = [];
    mockGetToken.mockReturnValue({ accessToken: "tok-1", refreshToken: "r-1" });
    client = new RealtimeClient();
  });

  afterEach(() => {
    client.stop();
    (globalThis as any).WebSocket = OriginalWebSocket;
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("无 token 时 start() 为 no-op，不建立连接", () => {
    mockGetToken.mockReturnValue(undefined);
    client.start();
    expect(FakeWebSocket.instances).toHaveLength(0);
  });

  it("start() 建立连接且 URL 不携带 token（首帧鉴权）", () => {
    client.start();
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(FakeWebSocket.instances[0].url).toBe(
      "ws://localhost:3000/api/system/ws"
    );
    expect(FakeWebSocket.instances[0].url).not.toContain("token");
  });

  it("连接建立后立即发送首帧 auth 消息（先于其它任何消息）", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    ws.simulateOpen();
    expect(ws.sent[0]).toBe(AUTH_FRAME);

    // 25s 后心跳 ping 跟在 auth 之后
    vi.advanceTimersByTime(25000);
    expect(ws.sent).toEqual([AUTH_FRAME, PING_FRAME]);
  });

  it("重复 start() 幂等：已有连接时不重复建连", () => {
    client.start();
    client.start();
    client.start();
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("stop() 后不自动重连（intentionalClose）", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    client.stop();
    // stop 内部触发 onclose，但主动关闭不应调度重连
    vi.advanceTimersByTime(30000);
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(ws.readyState).toBe(3);
  });

  it("服务端以 1008 关闭（鉴权失败）时不自动重连", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    ws.simulateOpen();
    ws.readyState = 3;
    // 模拟服务端鉴权失败：1008 关闭
    ws.onclose?.({ code: 1008 });
    // 退避窗口（含上限）内不应出现新连接
    vi.advanceTimersByTime(60000);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("意外断开后按指数退避重连（延时含 ±20% jitter，1s → [800, 1200]）", async () => {
    client.start();
    const ws1 = FakeWebSocket.instances[0];
    ws1.readyState = 3;
    ws1.onclose?.();
    // 800ms 下界之内不应重连
    await vi.advanceTimersByTimeAsync(799);
    expect(FakeWebSocket.instances).toHaveLength(1);
    // 1200ms 上界之内必然重连
    await vi.advanceTimersByTimeAsync(401);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it("重连退避延时始终落在 [0.8×base, min(1.2×base, 上限)] 区间内", () => {
    const setTimeoutSpy = vi.spyOn(globalThis, "setTimeout");
    client.start();

    let base = 1000;
    for (let round = 0; round < 5; round++) {
      const ws = FakeWebSocket.instances[round];
      ws.readyState = 3;
      ws.onclose?.();

      const delay = setTimeoutSpy.mock.calls.at(-1)![1] as number;
      expect(delay).toBeGreaterThanOrEqual(Math.round(base * 0.8));
      expect(delay).toBeLessThanOrEqual(
        Math.min(Math.round(base * 1.2), 15000)
      );

      // 推进到本次退避上限，触发下一轮建连
      vi.advanceTimersByTime(Math.min(Math.round(base * 1.2), 15000));
      base = Math.min(base * 2, 15000);
    }
    expect(FakeWebSocket.instances).toHaveLength(6);
  });

  it("pong 超时：2 个心跳周期无任何服务端消息时主动 close 并重连", async () => {
    client.start();
    const ws1 = FakeWebSocket.instances[0];
    ws1.simulateOpen();

    // 50s 内（含第 2 次心跳 tick）连接保持
    vi.advanceTimersByTime(50000);
    expect(ws1.readyState).toBe(1);
    expect(ws1.sent).toEqual([AUTH_FRAME, PING_FRAME, PING_FRAME]);

    // 第 3 个 tick（75s > 2×25s）判定假死：主动 close
    vi.advanceTimersByTime(25000);
    expect(ws1.readyState).toBe(3);

    // close 后走既有重连路径（1s ± 20% jitter）
    await vi.advanceTimersByTimeAsync(1200);
    expect(FakeWebSocket.instances).toHaveLength(2);
  });

  it("收到服务端消息会刷新活性基准，避免被误判假死", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    ws.simulateOpen();
    // 每 20s 收到一次业务推送（< 2×25s），连接应一直存活
    for (let i = 0; i < 6; i++) {
      vi.advanceTimersByTime(20000);
      ws.simulateMessage({ type: "notice", data: {} });
    }
    expect(ws.readyState).toBe(1);
    expect(FakeWebSocket.instances).toHaveLength(1);
  });

  it("on/off 事件总线按 type 派发且可取消订阅", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    const received: unknown[] = [];
    const handler = (payload: unknown) => received.push(payload);
    client.on("notice", handler);

    ws.simulateOpen();
    ws.simulateMessage({ type: "notice", data: { title: "hi" } });
    expect(received).toEqual([{ title: "hi" }]);

    client.off("notice", handler);
    ws.simulateMessage({ type: "notice", data: { title: "again" } });
    expect(received).toEqual([{ title: "hi" }]);
  });

  it("非法 JSON 与未知类型消息被静默忽略", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    const handler = vi.fn();
    client.on("notice", handler);
    ws.simulateOpen();

    expect(() => ws.simulateMessage("not-json")).not.toThrow();
    ws.simulateMessage({ noType: 1 });
    expect(handler).not.toHaveBeenCalled();
  });

  it("监听器抛异常不影响其它监听器", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    const bad = vi.fn(() => {
      throw new Error("listener bug");
    });
    const good = vi.fn();
    client.on("notice", bad);
    client.on("notice", good);
    ws.simulateOpen();

    expect(() =>
      ws.simulateMessage({ type: "notice", data: {} })
    ).not.toThrow();
    expect(good).toHaveBeenCalled();
  });

  it("心跳按 25s 间隔发送 ping", () => {
    client.start();
    const ws = FakeWebSocket.instances[0];
    ws.simulateOpen();
    vi.advanceTimersByTime(25000);
    expect(ws.sent).toEqual([AUTH_FRAME, PING_FRAME]);
    vi.advanceTimersByTime(25000);
    expect(ws.sent).toEqual([AUTH_FRAME, PING_FRAME, PING_FRAME]);
  });
});
