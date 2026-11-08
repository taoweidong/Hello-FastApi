# 部署

> 生产部署的完整操作手册在 `service/docs/guide/deployment.md`（Docker Compose / PostgreSQL / Redis），
> 数据库迁移见 `service/docs/guide/alembic.md`。本文只列部署相关的**检查单**。

[← 返回文档导航](../README.md)

---

## 1. 上线前检查单

| 项 | 要求 | 校验方式 |
|---|---|---|
| 密钥 | `SECRET_KEY`/`JWT_SECRET_KEY` 显式注入（compose 用 `${SECRET_KEY:?}` 强制） | 启动不报占位符错误 |
| API 文档 | 生产自动关闭（`/docs` 404 属预期） | `curl /docs` → 404 |
| 数据库 | PostgreSQL；执行 `alembic upgrade head`（勿用 create_all） | `python -m scripts.cli initdb` |
| 超管口令 | `initall` 创建的 admin/admin123 **必须立即改密** | 登录后修改 |
| Redis | 已设密码且未发布公网（compose 建议仅内网） | `redis-cli ping` |
| 限流 | `TRUSTED_PROXIES` 按反代拓扑配置 | 伪造 XFF 请求仍计数在同一桶 |
| 日志 | `logs/` 卷挂载持久化；管理员可经监控页远程查看 | 监控页「日志文件」 |
| 菜单种子 | `seedrbac` 已执行且超管可登录看到全量菜单 | 登录检查 |

## 2. 已知部署注意事项

- 多 worker 下 IP 规则热更新只作用于单个 worker（变更后建议滚动重启）；
- 缓存清理/日志浏览等管理端点要求**超级管理员**，普通管理员角色不满足时返回 403；
- WS 经反代需开启 upgrade 转发（Vite dev 代理已配置 `ws: true`）。
