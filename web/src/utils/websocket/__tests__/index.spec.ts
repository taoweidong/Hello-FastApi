/**
 * realtime WebSocket 客户端单元测试。
 *
 * 覆盖：幂等 start、无 token no-op、stop 语义（主动关闭不重连）、事件总线派发与异常隔离、
 * 非法消息静默。通过替换实例内部的 WebSocket 构造器避免真实网络。
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// 拦截 token 来源：start() 依据 getToken().accessToken 决定是否连接
const mockGetToken = vi.fn();
vi.mock("@/utils/auth", () => ({
  getToken: () => mockGetToken()
}));

import { RealtimeClient } from "../index";

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;
  static CONNECTING = 0;
  readyState = 0;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((evt: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
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

  it("start() 建立 WebSocket 连接并携带 token 查询参数", () => {
    client.start();
    expect(FakeWebSocket.instances).toHaveLength(1);
    expect(FakeWebSocket.instances[0].url).toContain(
      "/api/system/ws?token=tok-1"
    );
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

  it("意外断开后按指数退避重连", async () => {
    client.start();
    const ws1 = FakeWebSocket.instances[0];
    ws1.readyState = 3;
    ws1.onclose?.();
    // 第一次退避 1s
    await vi.advanceTimersByTimeAsync(1000);
    expect(FakeWebSocket.instances).toHaveLength(2);
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
    expect(ws.sent).toEqual([JSON.stringify({ type: "ping" })]);
    vi.advanceTimersByTime(25000);
    expect(ws.sent).toHaveLength(2);
  });
});
