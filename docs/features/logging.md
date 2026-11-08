# 日志体系

> 三路 loguru 输出 + HTTP 审计中间件 + 管理员远程文件浏览。
> 操作入口见[监控中心操作指导](../guide/monitoring.md#1-服务器监控monitorserver)。

[← 返回文档导航](../README.md)

---

## 1. 文件输出（`infrastructure/logging/logging_manager.py`）

目录：`service/logs/`（`settings.LOGS_DIR`，启动时自动创建）。

| 文件 | 内容 | 轮转 | 保留 |
|---|---|---|---|
| `app.log` | 业务日志（INFO+） | 10 MB | 7 天 |
| `error.log` | 错误及以上（含堆栈，生产关闭变量展开） | 10 MB | 7 天 |
| `access.log` | 请求访问行（方法/路径/状态/耗时/IP） | 10 MB | 7 天 |

另有 `backend_stdout.log` / `frontend_stderr.log` 等为启动脚本重定向产物（非框架管理）。

规范：全库统一 `from loguru import logger`，**禁止 print**（AGENTS.md 硬性规则）。

## 2. HTTP 审计中间件（`request_logging_middleware.py`）

- 所有请求写 access.log（含耗时 `X-Process-Time` 响应头）；
- **非 GET** 请求额外写 `sys_logs` 审计表：路径/方法/IP/浏览器/系统/创建人，
  请求体**先经敏感字段脱敏**（password/token/secret 等掩码化，上限 4000 字符）；
- 后台任务异步落库，不阻塞响应；登录/登出/刷新等高频或敏感路径在
  `_SKIP_LOG_PATH_PREFIXES` 中排除；
- 登录审计（`sys_userloginlog`）走**独立短会话**提交——业务事务回滚不会吞掉失败登录记录。

## 3. 远程浏览（管理员，免登录服务器）

服务器监控页「日志文件」卡片，或直接调用：

| 端点 | 说明 |
|---|---|
| `GET /api/system/log-files` | 清单（名称/字节/修改时间，倒序） |
| `GET /api/system/log-files/{name}/tail?lines=200` | 尾读（上限 1000 行，按块回扫） |
| `GET /api/system/log-files/{name}?download=true` | 内容 / 附件下载 |

- 权限：`require_superuser`（不做匿名静态挂载）；
- 路径安全：文件名白名单 + resolve 后必须位于 `LOGS_DIR` 内；
- 排查建议：先看 `error.log` 尾部定位异常，再用 `access.log` 尾部还原请求时间线。

## 4. 二次开发

- 业务代码记日志：`from loguru import logger`，`logger.info/warning/error`；
- 新增独立日志文件：在 `logging_manager` 增加 sink（保留/轮转策略照抄现有三路）；
- 新增审计排除路径：加入 `_SKIP_LOG_PATH_PREFIXES`（仅限无审计价值的读路径）。
