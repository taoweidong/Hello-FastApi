# 配置项速查

> 全部配置位于 `service/src/config/settings.py`，按 `APP_ENV` 加载 `.env.{environment}`。
> 解析优先级：构造参数 > `.env.{APP_ENV}` > `.env` > 模型默认值。
> 访问方式：`from src.config.settings import settings`（单例）。

[← 返回文档导航](../README.md)

---

## 应用

| 变量 | 默认 | 说明 |
|---|---|---|
| `APP_ENV` | development | development / production / testing |
| `DEBUG` | 按环境 | production=False |
| `APP_NAME` / `API_VERSION` | — | health 与 OpenAPI 展示 |
| `SECRET_KEY` / `JWT_SECRET_KEY` | 占位符 | ≥32 字符；**生产启动时校验占位符并 fail-fast** |
| `JWT_ALGORITHM` | HS256 | 令牌签名算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30（prod）/60（dev） | access 令牌有效期 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | refresh 令牌有效期 |
| `CORS_ORIGINS` | 逗号分隔 | 显式白名单（勿用 `*` + credentials） |

## 数据库 / Redis

| 变量 | 默认 | 说明 |
|---|---|---|
| `DATABASE_URL` | sqlite（dev/testing）/ PostgreSQL（prod） | 生产建议 PostgreSQL |
| `REDIS_URL` | redis://localhost:6379/1 | 缓存/限流/会话；不可用时各链路自动降级 |

## 限流

| 变量 | 默认 | 说明 |
|---|---|---|
| `RATE_LIMIT_TIMES` / `RATE_LIMIT_SECONDS` | 100 / 60 | 全局限流（SlowAPI 中间件） |
| `LOGIN_RATE_LIMIT` | 20/minute（prod） | 登录/注册专属（防爆破；testing 放宽） |
| `TRUSTED_PROXIES` | "" | 可信代理 IP/CIDR；空=直连，不信任 X-Forwarded-For |
| `RATE_LIMIT_STORAGE` | redis | memory 仅限单进程 |

详见 [限流方案](../features/rate-limit.md)。

## 缓存 TTL

| 变量 | 默认 | 说明 |
|---|---|---|
| `CACHE_PERMISSIONS_TTL` / `CACHE_USER_INFO_TTL` | 300s | 权限 / 用户信息 |
| `CACHE_MENU_ALL_TTL` | 600s | 菜单全量 |
| `CACHE_TOKEN_BLACKLIST_TTL` | 86400s | 黑名单兜底 TTL（实际取令牌剩余期） |
| `CACHE_DICT_TTL` | 3600s | 字典 |

## 路径

| 变量 | 值 | 说明 |
|---|---|---|
| `BASE_DIR` | `service/` | 根目录 |
| `SQL_DIR` | `service/sql/` | SQLite 库文件 |
| `LOGS_DIR` | `service/logs/` | 日志目录（管理员可远程浏览） |
| `UPLOAD_DIR` | `service/uploads/` | 头像等上传（`/media` 静态服务） |

## 环境差异要点

| 项 | development | production | testing |
|---|---|---|---|
| API 文档 /docs | 开 | **关**（main.py 按 is_production 关闭） | 开 |
| DEBUG / LOG_LEVEL | True / DEBUG | False / WARNING | True / DEBUG |
| 密钥占位符校验 | 跳过 | **fail-fast 拒绝启动** | 跳过 |
| LOGIN_RATE_LIMIT | 100/min | 20/min | 100000/min（用例不受限流） |
