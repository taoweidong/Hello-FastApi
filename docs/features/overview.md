# 功能总览

> 现有基础系统的功能地图：模块 → 前端页面 → 后端路由 → 权限码。
> 二次开发前先通读本章，确认要扩展的能力落在哪个模块。

[← 返回文档导航](../README.md)

---

## 1. 模块地图

| 业务模块 | 前端页面（`web/src/views/`） | 后端路由（`service/src/api/v1/`） | 核心权限码 | 说明 |
|---|---|---|---|---|
| 认证 | `login`、`welcome` | `auth_router.py` | 无（login/register 匿名） | 登录/登出/注册/刷新令牌/动态路由/个人安全日志 |
| 用户管理 | `system/user` | `user_router.py` | `user:view/add/edit/delete` | CRUD、重置密码、状态、分配角色、头像上传 |
| 角色管理 | `system/role` | `role_router.py` | `role:manage` | CRUD、菜单授权、**数据权限五档** |
| 菜单管理 | `system/menu` | `menu_router.py` | `menu:view/add/edit/delete` | 目录/页面/按钮三类节点 + 元数据，动态路由数据源 |
| 部门管理 | `system/dept` | `dept_router.py` | 部门相关码 | 树形部门，配合数据权限 |
| 岗位管理 | `system/post` | `post_router.py` | 岗位相关码 | 岗位 CRUD 与用户-岗位关联 |
| 字典管理 | `system/dictionary` | `dictionary_router.py` | `dictionary:view/add/edit/delete` | 字典类型 + 字典项（树 + 右键操作 + 新增主入口） |
| 参数配置 | `system/config` | `system_config_router.py` | 配置相关码 | 系统键值配置 |
| IP 规则 | `system/ip-rule` | `ip_rule_router.py` | IP 规则相关码 | 黑白名单（中间件每请求校验） |
| 日志管理 | `monitor/logs/*` | `log_router.py` | `log:view/delete` | 登录日志 / 操作日志（含清空与批量删除） |
| 服务器监控 | `monitor/server` | `monitor_router.py` | `monitor:view` + `monitor:manage` | CPU/内存/磁盘/系统/进程 + **日志文件远程浏览**（管理员） |
| 缓存监控 | `monitor/cache` | `monitor_router.py` | `monitor:view` + `monitor:manage` | Redis 状态 + **缓存分组清单与清理**（管理员） |
| 在线用户 | `monitor/online` | `monitor_router.py` | `monitor:view/manage` | 在线会话列表 + 强制下线 |
| 通知公告 | `system/notice` | `notice_router.py` + `ws_router.py` | 公告相关码 | 公告 CRUD + WebSocket 实时推送（顶栏铃铛） |
| 示例数据表 | `system/example-data` | `example_data_router.py` | `example:view/add/edit/delete` | **Univer 电子表格**单表 CRUD 示例（行内编辑/差异保存） |
| 个人中心 | `account-settings` | `auth_router.py`/`user_router.py` | 登录即可 | 资料/密码/头像/安全日志 |

## 2. 横切能力（不属于单一模块）

| 能力 | 实现位置 | 文档 |
|---|---|---|
| 认证与令牌 | JWT 双令牌 + Redis 黑名单 + 刷新轮换 | [认证与安全](auth-security.md) |
| 菜单式 RBAC | 菜单节点即权限（PERMISSION 类型 = 按钮码） | [RBAC 与数据权限](rbac.md) |
| 实时消息 | WebSocket 单例客户端 + RealtimePort 广播 | [实时消息](realtime.md) |
| 缓存体系 | CacheService + 按消费方拆分的窄端口 | [缓存体系](cache.md) |
| 限流 | SlowAPI 全局 + 登录专属中间件（可信代理 IP） | [限流方案](rate-limit.md) |
| 日志 | loguru 三路输出 + 审计中间件 + 远程浏览 | [日志体系](logging.md) |
| IP 黑白名单 | `IPFilterMiddleware`（app.state 缓存） | [RBAC 之外的运维能力](#3-运维能力速查) |

## 3. 运维能力速查

| 操作 | 入口 | 权限 |
|---|---|---|
| 日志文件清单 / 尾读 / 下载 | 服务器监控页「日志文件」卡片；`GET /log-files*` | 仅管理员（require_superuser） |
| 缓存分组清单 / 快速清理 / 清空全部 | 缓存监控页「缓存数据」区；`POST /cache-clear*` | 仅管理员 |
| 强制下线 | 在线用户页；`POST /online-logs/force-offline` | `monitor:manage` |
| IP 规则热更新 | IP 规则页增删改后自动刷新中间件缓存 | IP 规则相关码 |

## 4. 权限码约定

- 按钮级权限码 = 菜单树中 `menu_type=2 (PERMISSION)` 节点的 `name` 字段，
  由 `/get-async-routes` 下发到 `meta.auths`，前端用 `v-auth` 指令控制显隐；
- 后端在路由依赖上二次校验：`require_permission("xxx:yyy")`；
- 新增权限码必须同时落两处：菜单种子（`rbac_defaults.py`）+ 路由依赖（或前端 `v-auth`）。

详见 [RBAC 与数据权限](rbac.md)。
