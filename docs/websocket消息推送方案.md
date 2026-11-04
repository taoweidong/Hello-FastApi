# WebSocket 消息推送方案（通知公告实时推送）

> 范围（已与用户确认）：**复用现有通知公告模块**，管理员发布/启用公告时，所有在线登录用户经 WebSocket 实时收到，顶栏铃铛红点更新并弹窗提示；前端含自动重连。
> 不含「管理员主动广播任意消息」的通用接口（待后续扩展）。

## 1. 目标

- 后端新增 WebSocket 端点，支持按登录用户建立连接、鉴权、心跳保活。
- 当 `NoticeService` 创建/更新出一条 `is_active=1` 的公告时，向所有在线连接**广播**一条 `notice` 推送消息。
- 前端建立单例 WS 客户端：登录后自动连接、断线指数退避重连、心跳保活；收到 `notice` 消息后实时更新顶栏铃铛（红点 + 新条目）并弹出 `ElMessage` 提示。

## 2. 架构与数据流

```
[管理员] POST /api/system/notice/create (isActive=1)
        │
        ▼
NoticeService.create_notice ──► ws_manager.broadcast({type:"notice", data:{...}})
        │                                  │
        │                          [infrastructure/realtime/manager.py]  单例
        │                          active: dict[user_id, list[WebSocket]]
        ▼                                  ▼
   HTTP 200 ◄──────────────► 所有在线 WS 客户端收到 JSON 消息

[前端] App 启动/登录成功 → realtime.start()
        │  ws(s)://<location.host>/api/system/ws?token=<accessToken>   (dev 经 Vite /api 代理 + ws:true)
        ▼
  RealtimeClient：onopen / onmessage / onclose(重连) / 每25s ping
        │  收到 {type:"notice"} → 派发事件
        ▼
  lay-notice 订阅：prepend 到对应 tab（noticeType 2→公告 tab，1→通知 tab）
        + 红点 is-dot 显示 + ElMessage 弹窗 + 铃铛摇晃动画
```

## 3. 后端改动

### 3.1 新建 `service/src/infrastructure/realtime/manager.py`
- 单例 `ws_manager = ConnectionManager()`（模块级导出）。
- 数据结构：`_conns: dict[str, list[WebSocket]]`（同一用户多标签页 → 多连接）。
- 方法：
  - `async connect(user_id: str, ws: WebSocket)`
  - `disconnect(user_id: str, ws: WebSocket)`
  - `async send_to_user(user_id: str, message: dict)`
  - `async broadcast(message: dict)`（遍历全部连接 `await ws.send_json(message)`）
- 仅依赖 `fastapi.WebSocket` 与 `json`，**不反向依赖任何 service**，避免循环导入。

### 3.2 新建 `service/src/api/dependencies/ws_auth.py`
- `async def get_ws_user_id(token: str | None) -> str`：复用现有 `get_token_service()` / `get_cache_service()`，执行与 `get_current_user_id` 完全一致的四步校验（decode → 校验 access 类型 → 黑名单 → 提取 `sub`）。
- 失败抛 `UnauthorizedError`。后续可让 `auth.py` 的 `get_current_user_id` 也调用它以消除重复（可选，不在本次强制范围）。

### 3.3 新建 `service/src/api/v1/ws_router.py`
- 普通 `APIRouter`（`@router.websocket("/ws")`），在 `api/v1/__init__.py` 中以 `system_router.include_router(ws_router)` 注册 → 路径 `/api/system/ws`。
- 处理函数：
  1. 读 query `token`，`get_ws_user_id(token)`；失败则 `await websocket.accept()` 后 `await websocket.close(code=1008, reason="unauthorized")`，return。
  2. `await websocket.accept()` → `ws_manager.connect(user_id, ws)` → 发送欢迎 `{type:"connected", data:{user_id}}`。
  3. `while True:`
     - `text = await ws.receive_text()`
     - `msg = json.loads(text)`；若 `msg.get("type")=="ping"` → `await ws.send_json({type:"pong"})`（心跳）。
     - 其它类型暂忽略。
  4. `except WebSocketDisconnect:` → `ws_manager.disconnect(user_id, ws)`。

### 3.4 修改 `service/src/application/services/notice_service.py`
- `import ws_manager from src.infrastructure.realtime.manager`。
- `create_notice`：在 `return self._to_response(created)` 前，若 `dto.isActive == 1`，`await ws_manager.broadcast(self._notice_push(created))`。
- `update_notice`：`notice.update_info(...)` 后，若 `notice.is_active == 1`，同样广播。
- 新增私有方法 `_notice_push(notice) -> dict` 产出 `{type:"notice", data:<NoticeResponseDTO.model_dump()>, ts:<epoch>}`。
- **注意**：广播为尽力而为（best-effort），单个连接异常用 `try/except` 隔离，不影响 HTTP 响应。

## 4. 前端改动

### 4.1 `web/vite.config.ts`
- `/api` 代理增加 `ws: true`（开发态 WS 走同一代理；prod 同源无需代理）。

### 4.2 新建 `web/src/utils/websocket/index.ts`
- 单例 `realtime`（`class RealtimeClient`）：
  - `start()`：取 `getToken().accessToken`；无则 no-op。URL = `${location.protocol==="https:"?"wss":"ws"}://${location.host}/api/system/ws?token=${accessToken}`。
  - 原生 `WebSocket`；`onopen` 后启动 25s `setInterval` 发 `{type:"ping"}`。
  - `onmessage`：`JSON.parse` → 若有 `type` 则调用注册的 listeners（简单 `Map<string, Set<fn>>` 事件总线）。
  - `onclose/onerror`：清理定时器，非主动 logout 时按 `1→2→4→…→15s` 指数退避 `reconnect()`。
  - `stop()`：置 `intentional=true`，`ws.close()`，清定时器。
  - `on(event, cb)` / `off(event, cb)`：供组件订阅。

### 4.3 修改 `web/src/store/modules/user.ts`
- `login()` 成功（setToken 后）→ `realtime.start()`。
- `logOut()` → `realtime.stop()`（避免重连风暴）。

### 4.4 修改 `web/src/layout/components/lay-notice/index.vue`
- `onMounted`：保留现有 `fetchNotices()`（历史数据兜底）；新增 `realtime.on("notice", onRealtimeNotice)`。
- `onRealtimeNotice(payload)`：
  - 按 `payload.noticeType` 选 tab（2→key "1" 公告；1→key "2" 通知）。
  - 用与 `fetchNotices` 相同的 `toItem` 归一化后 `unshift` 到对应 tab 的 `list` 头部。
  - 调用 `message(...)`（来自 `@/utils/message`，即 ElMessage 封装）弹出标题+内容摘要。
  - 触发铃铛摇晃：给 `.header-notice-icon` 加一次 `pure-bell-ring` 动画 class（短暂）。
- `onBeforeUnmount`：`realtime.off("notice", onRealtimeNotice)`。

## 5. WS 协议约定

| 方向 | 类型 | 字段 |
|---|---|---|
| 客户端→服务端 | `ping` | `{type:"ping"}` |
| 服务端→客户端 | `pong` | `{type:"pong"}` |
| 服务端→客户端 | `connected` | `{type:"connected", data:{user_id}}` |
| 服务端→客户端 | `notice` | `{type:"notice", data:<公告DTO>, ts:<秒级时间戳>}` |
| 服务端→客户端(鉴权失败) | 关闭 | `code=1008, reason="unauthorized"` |

- 鉴权：query `token=accessToken`（JWT，URL 安全）。与 HTTP 共用同一套 JWT 校验 + 黑名单。
- 消息体统一 `application/json`（文本帧 `send_json`）。

## 6. 测试与验证

### 6.1 后端
- 新增 `tests/` 单测：
  - `manager` 连接/断开/广播（用 `fastapi.WebSocket` 的 `WebSocket` + `TestClient.websocket_connect` 或 mock）。
  - `ws_router` 鉴权：有效 token 可连、无效 token 被拒（close 1008）。
  - `NoticeService`：mock `ws_manager.broadcast`，断言 `isActive=1` 时广播、`isActive=0` 时不广播。
- 跑全量 `pytest` 确认无回归（基线 2171 passed）。

### 6.2 前端
- `pnpm typecheck` / `pnpm lint` / `pnpm build` 全绿。

### 6.3 E2E（Playwright，串行 workers=1）
- 新建 `web/e2e/crud-notice-ws.spec.ts`：
  1. `POST /api/system/login` 取 admin `accessToken`（或直接用 auth.setup 的存储态派生 token）。
  2. Node 侧用 `ws` 包（Playwright 依赖，已在 node_modules）连 `ws://127.0.0.1:8001/api/system/ws?token=...`。
  3. 收到 `{type:"connected"}` 后，`POST /api/system/notice/create`（isActive=1，标题含唯一串）。
  4. 断言 WS 在超时内收到 `{type:"notice", data.title === 唯一串}`。
  5. 关闭连接。
- 全量 E2E 保持通过（基线 75 passed），无回归。

### 6.4 手动冒烟
- 启动后端(8001)+前端(8899)，admin 发布一则公告 → 另一浏览器/隐身窗（已登录用户）顶栏铃铛红点出现、列表新增、弹窗提示。

## 7. 风险与回滚

- **Vite 代理 ws**：漏 `ws:true` 会导致 dev 下 WS 连不上；已列入必改项。
- **限流 429**：WS 连接不计入 slowapi（slowapi 只管 HTTP 路由），不受 `/api/system/ws` 限流；但创建公告的 HTTP 调用仍受 notice 限流，E2E 注意节奏。
- **广播阻塞**：单连接 `send_json` 异常已 `try/except` 隔离；管理器无持久化，进程重启后连接自然断开、前端重连。
- **回滚**：均为新增文件 + 局部改动，git revert 对应提交即可；`ws_manager` 为独立模块，移除引用不影响其它功能。

## 8. 涉及文件清单

新增：
- `service/src/infrastructure/realtime/manager.py`
- `service/src/api/dependencies/ws_auth.py`
- `service/src/api/v1/ws_router.py`
- `web/src/utils/websocket/index.ts`
- `web/e2e/crud-notice-ws.spec.ts`（测试）
- 后端 `tests/` 下 WS/通知广播单测

修改：
- `service/src/api/v1/__init__.py`（注册 ws_router）
- `service/src/application/services/notice_service.py`（发布即广播）
- `web/vite.config.ts`（代理加 `ws:true`）
- `web/src/store/modules/user.ts`（登录起/登出停）
- `web/src/layout/components/lay-notice/index.vue`（订阅实时通知）
