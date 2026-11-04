import { test, expect } from "@playwright/test";
import { WebSocket } from "ws";
import {
  API_BASE_URL,
  apiLogin,
  apiFetch,
  makeUniqueName
} from "./utils/helpers";

/**
 * 公告发布经 WebSocket 实时推送回归。
 *
 * 流程：API 登录取 token → 用 ws 包直连后端 /api/system/ws → 收到 connected →
 * 创建一则启用公告 → 断言在超时内收到 notice 推送且标题匹配 → 清理。
 *
 * 该用例验证「发布即推」链路：后端 NoticeService._push_notice → ws_manager.broadcast → WS 客户端。
 */
test("公告发布经 WebSocket 实时推送", async () => {
  const token = await apiLogin("admin", "admin123");
  const wsUrl =
    API_BASE_URL.replace(/^http/, "ws") +
    "/api/system/ws?token=" +
    encodeURIComponent(token);

  const ws = new WebSocket(wsUrl);
  const received: any[] = [];
  let connected = false;

  // 1) 建立连接并等待服务端 connected 握手（鉴权失败会 close 1008）
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(
      () => reject(new Error("WS 连接/握手超时（可能鉴权失败）")),
      15000
    );
    ws.on("open", () => {
      /* 等待 connected 消息 */
    });
    ws.on("message", data => {
      try {
        const msg = JSON.parse(data.toString());
        if (msg.type === "connected") {
          connected = true;
          clearTimeout(timer);
          resolve();
        } else if (msg.type === "notice") {
          received.push(msg);
        }
      } catch {
        /* ignore */
      }
    });
    ws.on("close", () => {
      if (!connected) {
        clearTimeout(timer);
        reject(new Error("WS 被关闭（可能 token 鉴权失败）"));
      }
    });
    ws.on("error", err => {
      clearTimeout(timer);
      reject(err);
    });
  });
  expect(connected, "WS 应成功鉴权并收到 connected").toBe(true);

  // 2) 创建一则启用公告（HTTP 200，返回公告 id 即成功）
  const title = makeUniqueName("wsnotice");
  const createRes = await apiFetch("POST", "/api/system/notice/create", {
    token,
    body: { title, content: "ws push content", noticeType: 1, isActive: 1 }
  });
  expect(createRes.status, "创建公告应返回 HTTP 200").toBe(200);
  const noticeId: string | undefined = createRes.body?.data?.id;
  expect(noticeId, "创建应返回公告 id").toBeTruthy();

  // 3) 断言在超时内收到 notice 推送且标题匹配
  const got = await new Promise<any>((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("未收到 notice 实时推送")), 10000);
    const check = setInterval(() => {
      const hit = received.find(m => m.data?.title === title);
      if (hit) {
        clearInterval(check);
        clearTimeout(t);
        resolve(hit);
      }
    }, 100);
  });
  expect(got.data.title, "推送标题应与创建标题一致").toBe(title);
  expect(got.type, "推送类型应为 notice").toBe("notice");

  // 4) 清理：删掉测试公告，关闭连接
  if (noticeId) {
    await apiFetch("DELETE", `/api/system/notice/${noticeId}`, { token });
  }
  ws.close();
});
