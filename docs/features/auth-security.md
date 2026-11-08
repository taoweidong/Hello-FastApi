# 认证与安全

> 登录态的生命周期：签发 → 使用 → 刷新轮换 → 登出吊销。
> 本文面向开发者理解认证链路；操作层面的登录/登出见[操作指导](../guide/authentication.md)。

[← 返回文档导航](../README.md)

---

## 1. 双令牌模型

| 令牌 | 有效期（生产） | 用途 | 传输 |
|---|---|---|---|
| access_token | 30 分钟（开发 60 分钟） | 请求鉴权（`Authorization: Bearer`） | Header |
| refresh_token | 7 天 | 换发新令牌对 | 刷新接口 Body |

- 算法：HS256（`JWT_ALGORITHM`），密钥 `JWT_SECRET_KEY`（生产强制显式配置，启动时 fail-fast 校验占位符）；
- 载荷：`sub`（用户 ID）、`username`、`exp`、`type`（access/refresh）。

## 2. 请求鉴权链路

```
Authorization: Bearer <access_token>
  → get_current_user_id：decode → type==access → 黑名单检查 → 提取 sub
  → get_current_active_user：缓存优先读取用户实体（user:info:{id}），校验 is_active
  → require_permission("xxx")：缓存优先校验权限（user:perms:{id}），超管快捷放行
```

缓存键失效由用户/角色变更主动触发（见[缓存体系](cache.md)），TTL 到期自然回源。

## 3. 刷新与轮换（rotation）

- `POST /refresh-token`：校验 refresh_token（类型/黑名单）后签发**新令牌对**，
  并把**旧 refresh_token 立即拉黑**——同一 refresh_token 只能使用一次（防重放）；
- 前端 axios 拦截器带并发防护（`isRefreshing` 请求队列），401 过期自动续期；
- ⚠️ 旧 refresh_token 在轮换后即失效：多标签页共享同一存储，正常使用无感。

## 4. 登出与吊销

- `POST /logout`：把 access_token（Header）与 refresh_token（Body，可选）**一并写入黑名单**，
  TTL 取令牌剩余有效期；
- 登出端点不强制要求有效令牌（`HTTPBearer(auto_error=False)`）——持有令牌即有权吊销它，
  前端在令牌已损坏场景下也能尽力完成服务端吊销；
- 黑名单校验 fail-open：Redis 不可用时放行（语义权衡已注释在 `cache_service.py`）。

## 5. 密码与凭证安全

- 哈希：bcrypt（12 轮），超过 72 字节的密码先做 SHA-256 预处理；
- 修改密码/重置密码均要求新密码 ≥8 位（DTO 层校验）；
- 注册与管理端建号对齐：用户名 ≥3 位、密码 ≥8 位、email 走 `EmailStr` 校验。

## 6. 审计

- 登录成功/失败均写 `sys_userloginlog`（失败记录经**独立短会话**提交，
  业务事务回滚不会吞掉审计记录）；
- 非 GET 请求体经**敏感字段脱敏**后写 `sys_logs` 审计表（password/token 等替换为掩码）；
- 生产环境错误日志关闭变量展开（loguru diagnose），避免敏感值落盘。

## 7. 相关端点

| 端点 | 说明 |
|---|---|
| `POST /login` / `/register` | 登录/注册（`LoginRateLimitMiddleware` 专属限流，见[限流](rate-limit.md)） |
| `POST /logout` | 吊销双令牌 |
| `POST /refresh-token` | 刷新 + 轮换 |
| `GET /mine` / `GET /mine-logs` | 当前用户信息 / 个人安全日志（分页） |
| `PUT /user/profile`、`POST /user/avatar` | 资料 / 头像（本站存储，`/media` 静态服务） |
