# 文档导航

> Hello-FastApi 全栈项目文档中心：FastAPI 后端（`service/`，DDD 四层）+
> Vue3 前端（`web/`，vue-pure-admin v7）。
> 首次接触从 [快速开始](getting-started/quick-start.md) 开始；
> 二次开发从 [设计架构](development/architecture.md) 与
> [后端 CRUD 开发指南](development/backend-crud-guide.md) 开始。

---

## 🚀 快速开始

| 文档 | 内容 |
|---|---|
| [快速开始](getting-started/quick-start.md) | 环境要求、前后端启动、初始化、首次登录、验证清单、常见问题 |

## 🖱️ 操作指导（系统使用者）

| 文档 | 内容 |
|---|---|
| [认证与账户](guide/authentication.md) | 登录/登出、改密、头像、个人安全日志 |
| [系统管理](guide/system-management.md) | 用户/角色/菜单/部门/岗位/字典/参数/IP 规则 操作要点与易错点 |
| [监控中心](guide/monitoring.md) | 服务器监控（含日志文件远程浏览）、缓存监控与清理、在线用户、日志管理 |
| [通知公告](guide/notifications.md) | 发布/编辑公告、实时推送机制说明 |

## 🧩 功能介绍（现有基础系统）

| 文档 | 内容 |
|---|---|
| [功能总览](features/overview.md) | 模块地图：页面 ↔ 路由 ↔ 权限码；横切能力与运维速查 |
| [认证与安全](features/auth-security.md) | 双令牌、刷新轮换、黑名单吊销、密码安全、审计 |
| [RBAC 与数据权限](features/rbac.md) | 菜单即权限、按钮权限码、数据权限五档、缓存一致性 |
| [实时消息](features/realtime.md) | WebSocket 公告推送设计与落地实现（含连接防护） |
| [缓存体系](features/cache.md) | 窄端口分层、键空间与 TTL、降级语义、管理操作、扩展方法 |
| [限流方案](features/rate-limit.md) | 全局限流 + 登录专属限流、可信代理 IP、fail-open 语义 |
| [日志体系](features/logging.md) | loguru 三路输出、审计中间件脱敏、日志远程浏览 |

## 🛠️ 开发指南（二次开发）

| 文档 | 内容 |
|---|---|
| [设计架构](development/architecture.md) | DDD 四层、依赖方向硬约束、端口-适配器、事务约定（UoW）、前后端分层 |
| [后端 CRUD 开发指南](development/backend-crud-guide.md) | 新增一个业务模块的全流程（13 文件清单 + 测试要求） |
| [前端开发指南](development/frontend-guide.md) | BaseApi/composables/动态路由/权限指令/新页面步骤 |
| [测试指南](development/testing.md) | 三层测试体系、契约对拍、提交门禁、可重复性红线 |
| [部署](development/deployment.md) | 上线检查单与部署注意事项（手册见 service/docs/guide/deployment.md） |

## 📌 参考

| 文档 | 内容 |
|---|---|
| [配置项速查](reference/settings.md) | 全部环境变量、默认值与环境差异要点 |
| [全量测试用例](reference/full-test-cases.md) | 人工/Agent 全量功能验证清单 + API 端点索引（v1.1） |

## 🗄️ 归档（历史快照与专项方案，不再活跃维护）

[archive/](archive/) 目录：历次质量评估报告、前端 UI/UX 优化方案与记录、
依赖升级方案、演示页面清理方案、OpenCode/Playwright 配置指南、pytest 误伤修复等。
内容以当时快照为准，可能与现状不一致，引用前请核对。

## 🔗 仓库内其他文档

- `AGENTS.md`（根目录）：AI 代理协作规范 + 后端架构速览 + 命令速查 —— **每次 AI 交互必读**
- `service/docs/guide/`：后端专项手册（Alembic / CLI / 环境配置 / 开发规范 / 测试 / 部署）
- `service/docs/design/`：后端设计资料（架构图 / 时序图 / 演进路线图）
- 根 `README.md`：项目简介与快速链接

## 📝 维护约定

1. 新功能合入时同步更新对应 features/guide 文档与 [全量测试用例](reference/full-test-cases.md) 端点索引；
2. 行为变更与文档不一致视为缺陷（AGENTS.md 协作规范第 4/5 条）；
3. 一次性方案/评估类文档进入 `archive/`，正文标注日期，不作现状陈述。
