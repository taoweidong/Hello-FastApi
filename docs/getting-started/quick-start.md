# 快速开始

> 目标：从零把 Hello-FastApi 前后端跑起来，并完成首次登录验证。
> 预计耗时：15 分钟（依赖已装好则 5 分钟）。

[← 返回文档导航](../README.md)

---

## 1. 环境要求

| 依赖 | 版本 | 说明 |
|---|---|---|
| Python | >= 3.10 | 后端 |
| Node.js | ^20.19.0 \|\| >=22.13.0 | 前端 |
| pnpm | >= 9 | 前端包管理（`preinstall` 强制 pnpm，npm/yarn 会被拒绝） |
| uv | 最新 | Python 虚拟环境与依赖管理 |
| Redis | 5+ | 缓存/限流/在线会话（可选，缺省自动降级） |

> Redis 未启动时系统可正常运行：缓存、限流、在线会话、WebSocket 登记均自动降级，
> 但监控页的 Redis 状态、缓存数据清单会显示"缓存服务不可用"。

## 2. 后端启动

```bash
cd service
uv venv --python 3.10
.venv\Scripts\activate                # Windows；Linux/Mac: source .venv/bin/activate
uv pip install -e ".[dev]"

# 一键初始化：建表(Alembic) → 测试数据 → RBAC 菜单/角色 → 超级管理员
python -m scripts.cli initall

# 启动开发服务器
python -m scripts.cli runserver       # http://localhost:8000
```

验证：`curl http://127.0.0.1:8000/health` 返回 `{"status":"healthy",...}`。

## 3. 前端启动

```bash
cd web
pnpm install
pnpm dev                              # http://localhost:8848（端口可在 .env.development 调整）
```

Vite 已配置代理：`/api` 与 `/media` → `http://127.0.0.1:8000`（含 WebSocket 转发），
可用环境变量 `VITE_BACKEND_PORT` 覆盖后端端口。

## 4. 首次登录

- 地址：http://127.0.0.1:8848
- 账号：`admin` / `admin123`（`initall` 创建的超级管理员）
- 登录后动态路由由后端 `/get-async-routes` 下发，左侧菜单即全部业务模块。

## 5. 启动验证清单

| 检查项 | 预期 |
|---|---|
| 后端 health | `{"status":"healthy","version":"v1"}` |
| 前端首页 | 登录页正常渲染，验证码可刷新 |
| 登录 | 进入欢迎页，左侧出现全部菜单 |
| 服务器监控 `/monitor/server` | CPU/内存/磁盘/系统信息 + 日志文件卡片（管理员） |
| 缓存监控 `/monitor/cache` | Redis 运行状态 + 缓存数据清单（Redis 已启动时） |

## 6. 常见问题

| 现象 | 原因与处理 |
|---|---|
| 后端启动报密钥错误 | 生产环境（APP_ENV=production）强制要求显式密钥；开发环境使用 `.env.development` 默认值即可 |
| 登录后菜单为空 | 未执行 `initall`/`seedrbac`，或 Redis 不可用导致菜单缓存降级异常——重跑 `seedrbac` |
| 前端安装失败 `only-allow pnpm` | 项目强制 pnpm，改用 `pnpm install` |
| 8000 端口被占用 | 上一实例未退出：`taskkill /F /T /PID <pid>`（注意 uvicorn 子进程） |
| 字典/角色页按钮不显示 | 按钮按权限码显隐（`v-auth`），确认当前角色已分配对应菜单权限节点 |

## 7. 下一步

- 了解系统有哪些功能：[功能总览](../features/overview.md)
- 日常操作指导：[操作指导目录](../guide/authentication.md)
- 基于本系统二次开发：[开发指南目录](../development/architecture.md)
