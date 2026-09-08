# Hello-FastApi 全量测试用例文档

> 版本：v1.0 ｜ 最后更新：2026-08-21
> 适用仓库：`e:\GitHub\Hello-FastApi`（FastAPI 后端 `service/` + Vue3 前端 `web/`）
> 用途：供人工或 AI Agent 按本文档执行全量功能验证，保证所有功能可用。

---

## 目录

1. [测试目标与验收标准](#1-测试目标与验收标准)
2. [环境准备](#2-环境准备)
3. [测试账号与认证约定](#3-测试账号与认证约定)
4. [接口通用约定](#4-接口通用约定)
5. [后端 API 测试用例](#5-后端-api-测试用例)
6. [前端功能测试用例](#6-前端功能测试用例)
7. [自动化回归执行方案](#7-自动化回归执行方案)
8. [本次验证执行结果（2026-08-21）](#8-本次验证执行结果2026-08-21)
9. [已知问题与注意事项](#9-已知问题与注意事项)
10. [附录：API 端点索引（76 个）](#10-附录api-端点索引76-个)

---

## 1. 测试目标与验收标准

**目标**：验证后端 API 76 个端点与前端全部功能页面的正确性，确保 CRUD、认证鉴权、树形加载、日志监控、系统配置等核心链路可用。

**验收标准**（全部满足即通过）：

| 编号 | 标准 | 判定方式 |
|---|---|---|
| AC-1 | 后端可用 `pytest` 全量测试通过 | `2143 passed`，退出码 0 |
| AC-2 | 后端 9 大模块 CRUD 冒烟全部 2xx | 冒烟脚本输出无 FAIL |
| AC-3 | 前端 `vue-tsc --noEmit` 通过 | 退出码 0 |
| AC-4 | 前端 ESLint 通过 | `--max-warnings 0` 退出码 0 |
| AC-5 | 前端生产构建成功 | `vite build` 退出码 0 |
| AC-6 | 登录 → 动态路由 → 各页面可打开可操作 | 前端人工/E2E 验证 |

---

## 2. 环境准备

### 2.1 后端依赖（Python >= 3.10，uv）

```bash
cd e:\GitHub\Hello-FastApi\service
uv venv --python 3.10
.venv\Scripts\activate            # Windows；Linux/Mac 用 source .venv/bin/activate
uv pip install -e ".[dev]"
```

> 注：Windows PowerShell 不支持 `&&`，多条命令用 `;` 分隔。

### 2.2 数据库初始化（一次性）

```bash
# 推荐：一键初始化（建表 + 种子数据 + 角色菜单 + 超级管理员）
.\.venv\Scripts\python.exe -m scripts.cli initall

# 或分步执行
.\.venv\Scripts\python.exe -m scripts.cli initdb       # Alembic upgrade head
.\.venv\Scripts\python.exe -m scripts.cli seeddata     # 日志等测试数据
.\.venv\Scripts\python.exe -m scripts.cli seedrbac     # 默认菜单 + 角色（必须在 seeddata 之后）
.\.venv\Scripts\python.exe -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
```

### 2.3 启动后端服务

```bash
.\.venv\Scripts\python.exe -m scripts.cli runserver    # 默认 http://localhost:8000
```

- API 文档：http://localhost:8000/docs（Swagger）、http://localhost:8000/openapi.json
- 健康检查：http://localhost:8000/health

### 2.4 前端依赖与启动（Node `^20.19.0 || >=22.13.0`）

```bash
cd e:\GitHub\Hello-FastApi\web
pnpm install                 # 需 pnpm >= 9
pnpm dev                     # 默认端口 8848（VITE_PORT，见 .env.development）
```

> **本机注意**：`pnpm` 可能不在 PATH（已通过 corepack 提供 11.22.0）。可执行
> `& "D:\Program Files\nodejs\corepack.cmd" pnpm <cmd>`，或直接用 `node_modules/.bin/` 下的
> 二进制（如 `.\node_modules\.bin\vite.cmd dev`）。
> ⚠️ pnpm 11 检测到 node_modules 为旧版布局会要求重建（无 TTY 时中断），**不要轻易
> 直接运行 `pnpm install` 重建依赖**；静态检查/构建请用 `npm run <script>` 或 `.bin` 二进制绕过。

### 2.5 Redis（可选）

- 默认连接 `redis://localhost:6379/0`（`settings.REDIS_URL`）。
- **缺失时系统自动降级**：缓存读写、限流、在线用户等全部降级放行，功能不受影响，
  但每个请求额外产生约 3 次 socket 超时等待（每次 1s，见 `settings.REDIS_CONNECT_TIMEOUT` /
  `REDIS_SOCKET_TIMEOUT`，可通过 `.env.*` 调大或调小）。
- 配置项（`service/src/config/settings.py`）：
  - `REDIS_URL`
  - `REDIS_CONNECT_TIMEOUT`（默认 1.0 秒）
  - `REDIS_SOCKET_TIMEOUT`（默认 1.0 秒）

### 2.6 前端代理

Vite 将 `/api` 代理到 `http://localhost:8000`（`web/vite.config.ts`）。**必须先启动后端**，前端才能联调。

---

## 3. 测试账号与认证约定

| 项目 | 值 |
|---|---|
| 默认超级管理员 | `admin` / `admin123`（`initall` 后存在，拥有 `admin` 角色） |
| 登录接口 | `POST /api/system/login` |
| 鉴权方式 | `Authorization: Bearer <data.accessToken>` |

```bash
# 获取 token 示例（PowerShell）
$body = '{"username":"admin","password":"admin123"}'
$resp = Invoke-RestMethod -Uri http://localhost:8000/api/system/login -Method Post -Body $body -ContentType 'application/json'
$token = $resp.data.accessToken
$headers = @{ Authorization = "Bearer $token" }
```

**认证断言通用规则**：
- 未带/带错误 token 请求受保护端点 → `401`；token 过期后 `refresh-token` 可换新。
- 带正确 token → 业务端点返回 `200/201`，body 结构 `{"code":0,"message":"...","data":...}`。

---

## 4. 接口通用约定

- **基础前缀**：`/api/system`（docs 在 `/docs`、`/redoc`）。
- **响应包装**（`src/api/common/response_builder.py`）：
  - 单条数据：`{"code":0,"message":"success","data":{...}}`
  - 分页列表（用户/角色/菜单/部门/公告/岗位/IP规则/配置/日志等）：`data = {"list":[...],"total":N,"pageSize":N,"currentPage":N}`
  - ⚠️ **例外：字典列表端点的 `data` 直接是数组**（非 `list` 嵌套）。
- **列表接口**：全部为 `POST {prefix}`（body 传 `pageNum`/`pageSize`/筛选条件），不是 GET。
- **创建接口**：`POST {prefix}/create`；**用户创建固定返回 201**（REST 语义），其余模块 200。
- **详情接口**：`GET {prefix}/{id}` 存在；⚠️ **menu / dept / dictionary 三个模块无 GET 详情端点**（仅有 PUT/DELETE）。
- **删除**：`DELETE {prefix}/{id}`；批量删除 `POST {prefix}/batch-delete`，body `{"ids":[...]}`。
- **状态修改**：`PUT {prefix}/{id}/status`，body 传 `{"isActive": 0|1}` 等状态字段。
- **登出**：`POST /logout` 需带 `Content-Type: application/json`（body 可为 `{}`）。
- **token 刷新**：`POST /refresh-token`，body `{"refreshToken": "<refreshToken>"}`。
- 取请求体中 id 的场景：创建响应 `data.id` 即为 36 位 UUID 字符串。

---

## 5. 后端 API 测试用例

> 使用说明：以下用例均可通过 curl / httpx / Postman 执行；每节给出「方法 + 路径 + 关键 body + 期望状态码 + 断言」。
> 冒烟参考脚本：`service/_smoke_api.py`（覆盖 9 模块 CRUD + 认证/树形/日志/监控全链路，见 [7.3](#73-api-冒烟脚本service_smoke_apipy)）。

### 5.1 认证模块

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| AUTH-01 登录成功 | `POST /login` | `{"username":"admin","password":"admin123"}` | 200 | `data.accessToken`、`data.refreshToken` 非空，`code==0` |
| AUTH-02 密码错误 | `POST /login` | `{"username":"admin","password":"wrong"}` | 200? 或 401 | `code!=0`，message 提示密码错误（按实现） |
| AUTH-03 无 token 访问 | `GET /mine`（无 Authorization） | - | 401 | 未鉴权被拦截 |
| AUTH-04 刷新 token | `POST /refresh-token` | `{"refreshToken":"<登录返回>"}` | 200 | 返回新的 `accessToken` |
| AUTH-05 注册新用户 | `POST /register` | `{"username":"reg_case1","password":"Test123456"}` | 200 | `message` 含「注册成功」；用户名可复用，勿超长 |
| AUTH-06 登出 | `POST /logout`，头含 `Content-Type: application/json` | `{}` | 200 | `code==0` |

### 5.2 用户模块（前缀 `/user`）

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| USER-01 分页列表 | `POST /user` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 为数组，`data.total` 为数字 |
| USER-02 创建用户 | `POST /user/create` | `{"username":"t_case1","password":"Test123456","nickname":"测试用户1"}` | **201** | `data.id` 为 36 位 UUID |
| USER-03 用户详情 | `GET /user/{id}` | - | 200 | `data.username` 与创建一致 |
| USER-04 更新用户 | `PUT /user/{id}` | `{"nickname":"更新后的昵称"}` | 200 | 列表/详情中 nickname 已变更 |
| USER-05 删除用户 | `DELETE /user/{id}` | - | 200 | 再查列表该 id 不存在 |
| USER-06 批量删除 | `POST /user/batch-delete` | `{"ids":[id1,id2]}` | 200 | `code==0` |
| USER-07 重置密码 | `PUT /user/{id}/reset-password` | `{"newPassword":"NewPass123"}` | 200 | `code==0`；旧密码登录失败、新密码可登录（可选验证） |
| USER-08 修改状态 | `PUT /user/{id}/status` | `{"isActive":0}` | 200 | 列表状态字段变更 |
| USER-09 分配角色 | `POST /user/assign-role` | `{"user_id":"<uid>","role_ids":["<roleId>"]}` | 200 | `code==0` |
| USER-10 修改密码(本人) | `POST /user/change-password` | `{"oldPassword":"admin123","newPassword":"NewPass123"}` | 200 | `code==0`（⚠️ 会改变当前登录密码，测试后改回） |
| USER-11 更新个人资料 | `PUT /user/profile` | `{"nickname":"新昵称","email":"a@b.com","phone":"13800000000","description":"简介"}` | 200 | `GET /mine` 中字段已更新 |
| USER-12 上传头像 | `POST /user/avatar`（multipart/form-data，字段 `file`） | 图片文件 | 200 | `data.avatar` 返回头像 URL |
| USER-13 当前用户信息 | `GET /user/info` | - | 200 | 返回用户扩展信息 |
| USER-14 所有角色下拉 | `GET /list-all-role` | - | 200 | `data` 为角色数组 |
| USER-15 用户角色ID列表 | `POST /list-role-ids` | `{"userId":"<uid>"}` | 200 | `data` 为角色 id 数组 |
| USER-16 已分配岗位ID | `GET /post/user/{userId}` | - | 200 | `data` 为岗位 id 数组 |

> 取 `uid`：`POST /user` 分页列表按 `username` 匹配；⚠️ `GET /mine` 返回扁平字段（avatar/username/nickname/email/phone/description），**不含 id**。

### 5.3 角色模块（前缀 `/role`）

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| ROLE-01 分页列表 | `POST /role` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| ROLE-02 创建角色 | `POST /role/create` | `{"name":"测试角色A","code":"role_a"}` | 200 | `data.id` UUID |
| ROLE-03 角色详情 | `GET /role/{id}` | - | 200 | `data.code == "role_a"` |
| ROLE-04 更新角色 | `PUT /role/{id}` | `{"name":"测试角色A-改"}` | 200 | 详情已更新 |
| ROLE-05 修改状态 | `PUT /role/{id}/status` | `{"isActive":0}` | 200 | 状态变更 |
| ROLE-06 删除角色 | `DELETE /role/{id}` | - | 200 | 列表无此 id |
| ROLE-07 角色菜单树 | `POST /role-menu` | `{}`（可空 body） | 200 | `data` 菜单树 |
| ROLE-08 角色菜单ID | `POST /role-menu-ids` | `{"id":"<roleId>"}` | 200 | `data` 菜单 id 数组 |
| ROLE-09 保存角色菜单 | `POST /role/{roleId}/menus` | `{"menuIds":["<menuId>",...]}` | 200 | `code==0` |
| ROLE-10 数据权限范围 | `POST /role/{roleId}/data-scope` | `{"dataScope":1,"deptIds":[]}` | 200 | `code==0` |

### 5.4 菜单模块（前缀 `/menu`）⚠️ 无 GET 详情

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| MENU-01 分页列表 | `POST /menu` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| MENU-02 创建菜单 | `POST /menu/create` | `{"name":"测试菜单X","menuType":1,"path":"/test/x"}` | 200 | `data.id` UUID |
| MENU-03 更新菜单 | `PUT /menu/{id}` | `{"name":"测试菜单X-改"}` | 200 | 树/列表中可见新名称 |
| MENU-04 删除菜单 | `DELETE /menu/{id}` | - | 200 | 树中消失 |
| MENU-05 菜单树 | `GET /menu/tree` | - | 200 | `data` 为树结构数组 |
| MENU-06 当前用户菜单 | `GET /menu/user-menus` | - | 200 | `data` 为树结构数组 |

### 5.5 部门模块（前缀 `/dept`）⚠️ 无 GET 详情

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| DEPT-01 分页列表 | `POST /dept` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| DEPT-02 创建部门 | `POST /dept/create` | `{"name":"测试部门Y"}` | 200 | `data.id` UUID |
| DEPT-03 更新部门 | `PUT /dept/{id}` | `{"name":"测试部门Y-改"}` | 200 | 数据已更新 |
| DEPT-04 删除部门 | `DELETE /dept/{id}` | - | 200 | 列表无此 id |
| DEPT-05 部门树 | `GET /dept/tree` | - | 200 | `data` 树结构数组 |

### 5.6 字典模块（前缀 `/dictionary`）⚠️ 无 GET 详情；列表 `data` 为裸数组

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| DICT-01 分页列表 | `POST /dictionary` | `{"pageNum":1,"pageSize":10}` | 200 | ⚠️ `data` 为数组（非 `list` 字段） |
| DICT-02 创建字典 | `POST /dictionary/create` | `{"name":"dict_case1","label":"用例标签","value":"case1","sort":1}` | 200 | `data.id` UUID |
| DICT-03 更新字典 | `PUT /dictionary/{id}` | `{"label":"用例标签-改"}` | 200 | 数据已更新 |
| DICT-04 删除字典 | `DELETE /dictionary/{id}` | - | 200 | 列表无此 id |
| DICT-05 按类型取字典项 | `GET /dictionary/type/{dictName}` | - | 200 | 如 `sys_user_sex`，`data` 为字典项数组 |
| DICT-06 按名称取字典 | `POST /dictionary/getByName` | `{"name":"sys_user_sex"}` | 200 | `data` 为字典项数组 |

### 5.7 公告模块（前缀 `/notice`）

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| NOTICE-01 分页列表 | `POST /notice` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| NOTICE-02 创建公告 | `POST /notice/create` | `{"title":"测试公告","content":"内容","noticeType":1}` | 200 | `data.id` UUID |
| NOTICE-03 公告详情 | `GET /notice/{id}` | - | 200 | `data.title` 一致 |
| NOTICE-04 更新公告 | `PUT /notice/{id}` | `{"title":"测试公告-改"}` | 200 | 详情已更新 |
| NOTICE-05 删除公告 | `DELETE /notice/{id}` | - | 200 | 列表无此 id |
| NOTICE-06 批量删除 | `POST /notice/batch-delete` | `{"ids":[id]}` | 200 | `code==0` |
| NOTICE-07 最新公告 | `GET /notice/latest` | - | 200 | `data` 为启用公告列表（顶栏铃铛） |

### 5.8 岗位模块（前缀 `/post`）

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| POST-01 分页列表 | `POST /post` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| POST-02 创建岗位 | `POST /post/create` | `{"postCode":"case1","postName":"测试岗位"}` | 200 | `data.id` UUID |
| POST-03 岗位详情 | `GET /post/{id}` | - | 200 | `data.postCode` 一致 |
| POST-04 更新岗位 | `PUT /post/{id}` | `{"postName":"测试岗位-改"}` | 200 | 详情已更新 |
| POST-05 删除岗位 | `DELETE /post/{id}` | - | 200 | 列表无此 id |
| POST-06 批量删除 | `POST /post/batch-delete` | `{"ids":[id]}` | 200 | `code==0` |
| POST-07 岗位下拉选项 | `GET /post/options` | - | 200 | `data` 为启用岗位数组 |
| POST-08 用户已分配岗位 | `GET /post/user/{userId}` | - | 200 | `data` 为岗位 id 数组 |

### 5.9 IP 规则模块（前缀 `/ip-rule`）

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| IP-01 分页列表 | `POST /ip-rule` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| IP-02 创建规则 | `POST /ip-rule/create` | `{"ipAddress":"10.9.9.9","ruleType":"blacklist","reason":"测试"}` | 200 | ⚠️ `ruleType` 必须是字符串 `"blacklist"` / `"whitelist"`（传数字会 422）；`data.id` UUID |
| IP-03 规则详情 | `GET /ip-rule/{id}` | - | 200 | `data.ipAddress` 一致 |
| IP-04 更新规则 | `PUT /ip-rule/{id}` | `{"reason":"测试改"}` | 200 | 详情已更新 |
| IP-05 删除规则 | `DELETE /ip-rule/{id}` | - | 200 | 列表无此 id |
| IP-06 批量删除 | `POST /ip-rule/batch-delete` | `{"ids":[id]}` | 200 | `code==0` |
| IP-07 清空规则 | `POST /ip-rule/clear` | - | 200 | `code==0` |

### 5.10 系统配置模块（前缀 `/config`）

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| CONFIG-01 分页列表 | `POST /config` | `{"pageNum":1,"pageSize":10}` | 200 | `data.list` 数组 |
| CONFIG-02 创建配置 | `POST /config/create` | `{"key":"case.key1","value":"1","description":"测试"}` | 200 | `data.id` UUID |
| CONFIG-03 配置详情 | `GET /config/{id}` | - | 200 | `data.key` 一致 |
| CONFIG-04 更新配置 | `PUT /config/{id}` | `{"value":"2"}` | 200 | 详情已更新 |
| CONFIG-05 删除配置 | `DELETE /config/{id}` | - | 200 | 列表无此 id |

### 5.11 日志与监控模块

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| LOG-01 登录日志列表 | `POST /login-logs` | `{"pageNum":1,"pageSize":5}` | 200 | `data.list` 数组 |
| LOG-02 操作日志列表 | `POST /operation-logs` | `{"pageNum":1,"pageSize":5}` | 200 | `data.list` 数组 |
| LOG-03 系统日志列表 | `POST /system-logs` | `{"pageNum":1,"pageSize":5}` | 200 | `data.list` 数组 |
| LOG-04 系统日志详情 | `POST /system-logs-detail` | `{"id":"<logId>"}` | 200 | `data` 含日志详情字段 |
| LOG-05 在线用户列表 | `POST /online-logs` | `{"pageNum":1,"pageSize":5}` | 200 | `data.list` 数组 |
| LOG-06 强制下线 | `POST /online-logs/force-offline` | `{"id":"<在线会话id>"}` | 200 | `code==0`，目标用户离线 |
| LOG-07 批量删除登录日志 | `POST /login-logs/batch-delete` | `{"ids":[id]}` | 200 | `code==0` |
| LOG-08 清空登录日志 | `POST /login-logs/clear` | - | 200 | `code==0` |
| LOG-09 批量删除操作日志 | `POST /operation-logs/batch-delete` | `{"ids":[id]}` | 200 | `code==0` |
| LOG-10 清空操作日志 | `POST /operation-logs/clear` | - | 200 | `code==0` |
| MON-01 服务器监控 | `GET /server-info` | - | 200 | `data` 含 cpu/memory/disk/system/process |
| MON-02 缓存监控 | `GET /cache-info` | - | 200 | ⚠️ Redis 缺失时 `data.connected==false`（降级响应，仍 200） |
| MON-03 动态路由 | `GET /get-async-routes` | - | 200 | `data` 为菜单树（登录后可拉取） |
| MON-04 卡片列表 | `POST /get-card-list` | `{}` | 200 | `data.list` 数组 |
| MON-05 地图信息 | `GET /get-map-info` | - | 200 | `data` 为地图配置（stub 演示接口） |
| MON-06 健康检查 | `GET /health`（无前缀 `http://localhost:8000/health`） | - | 200 | body 含 `status` 正常 |

### 5.12 个人中心

| 用例 | 方法/路径 | 请求体 | 期望 | 断言要点 |
|---|---|---|---|---|
| MINE-01 我的信息 | `GET /mine` | - | 200 | `data.username=="admin"`；⚠️ 无 `id` 字段 |
| MINE-02 我的安全日志 | `GET /mine-logs` | - | 200 | `data.list` 数组（可与 `?pageNum/pageSize` 配合） |

---

## 6. 前端功能测试用例

> 页面路径即 `web/src/views/` 下的目录。动态路由由后端 `/get-async-routes` 返回，登录后渲染。
> 每个用例的「关键操作」按页面实际交互执行，结果通过 UI 反馈与 Network 响应共同确认。

### 6.1 登录与整体链路

| 用例 | 页面 | 关键操作 | 期望结果 |
|---|---|---|---|
| FE-01 登录页 | `/login` | 输入 admin/admin123 点登录 | 跳转首页；本地存储 `accessToken/refreshToken`；顶部显示用户昵称 |
| FE-02 错误登录 | `/login` | 错误密码登录 | 提示错误，未跳转 |
| FE-03 动态路由 | 全局 | 登录后检查侧边菜单 | 菜单与 `GET /get-async-routes` 返回一致；点击各菜单能打开页面 |
| FE-04 登出 | 全局 | 点击头像 → 退出登录 | 回到登录页，清理本地 token |
| FE-05 token 刷新 | 全局 | 页面停留至 accessToken 过期后再操作 | 自动 `refresh-token` 后请求成功，不强制跳登录 |

### 6.2 系统管理页面

| 用例 | 页面 | 关键操作 | 期望结果 | 关联 API |
|---|---|---|---|---|
| FE-10 用户管理 | `/system/user` | 列表加载/搜索/新增/编辑/删除/批量删除/重置密码/分配角色/调整状态 | 表格分页正确；新增后立即刷新可见；删除确认后行消失 | USER-01~09 |
| FE-11 角色管理 | `/system/role` | 列表/新增/编辑/删除/状态/权限分配 | CRUD 生效；权限弹窗勾选菜单保存后重登生效 | ROLE-01~10 |
| FE-12 菜单管理 | `/system/menu` | 树形列表/新增/编辑/删除 | 树结构正确；新增菜单后重新登录可在侧边栏看到 | MENU-01~06 |
| FE-13 部门管理 | `/system/dept` | 树形列表/新增/编辑/删除 | 树结构正确，CRUD 生效 | DEPT-01~05 |
| FE-14 字典管理 | `/system/dictionary` | 列表/新增/编辑/删除/按类型查看字典项 | CRUD 生效；字典项下拉在其他表单可用 | DICT-01~06 |
| FE-15 公告管理 | `/system/notice` | 列表/新增/编辑/删除/批量删除 | CRUD 生效；顶栏铃铛显示最新启用公告 | NOTICE-01~07 |
| FE-16 岗位管理 | `/system/post` | 列表/新增/编辑/删除/批量删除 | CRUD 生效；用户表单岗位下拉可选 | POST-01~08 |
| FE-17 IP 规则 | `/system/ip-rule` | 列表/新增（黑/白名单）/编辑/删除/清空 | CRUD 生效；新增规则后对应 IP 被拦/放行（可选验证） | IP-01~07 |
| FE-18 系统配置 | `/system/config` | 列表/新增/编辑/详情/删除 | CRUD 生效；details 展示 | CONFIG-01~05 |

### 6.3 监控页面

| 用例 | 页面 | 关键操作 | 期望结果 | 关联 API |
|---|---|---|---|---|
| FE-20 服务器监控 | `/monitor/server` | 打开页面 | CPU/内存/磁盘/系统/进程指标渲染 | MON-01 |
| FE-21 缓存监控 | `/monitor/cache` | 打开页面 | 指标卡片渲染；Redis 缺失时展示降级提示 | MON-02 |
| FE-22 登录日志 | `/monitor/logs/login` | 列表加载/筛选/批量删除/清空 | 展示最近的登录记录 | LOG-01/07/08 |
| FE-23 操作日志 | `/monitor/logs/operation` | 列表加载/筛选/批量删除/清空 | 展示操作记录（增删改产生的新记录可见） | LOG-02/09/10 |
| FE-24 系统日志 | `/monitor/logs/system` | 列表加载/点击查看详情 | 详情弹窗展示完整日志 | LOG-03/04 |
| FE-25 在线用户 | `/monitor/online` | 列表加载/强制下线 | 在线列表展示；强制下线后刷新消失 | LOG-05/06 |

### 6.4 个人中心与基础页面

| 用例 | 页面 | 关键操作 | 期望结果 | 关联 API |
|---|---|---|---|---|
| FE-30 账号设置-资料 | `/account-settings` | 修改昵称/邮箱/电话/简介并保存 | 保存成功提示；`GET /mine` 数据同步 | USER-11 |
| FE-31 账号设置-头像 | `/account-settings` | 上传头像 | 头像即时更新显示 | USER-12 |
| FE-32 账号设置-密码 | `/account-settings` | 输入旧密码/新密码修改 | 成功提示；新密码可登录（注意测试后还原） | USER-10 |
| FE-33 账号设置-安全日志 | `/account-settings` | 查看安全日志 | 条列展示登录/操作记录 | MINE-02 |
| FE-34 欢迎页 | `/welcome` | 打开页面 | 统计卡片、图表、公告滚动等渲染 | MON-04 等 |
| FE-35 权限-页面 | `/permission/page` | 打开 | 按角色渲染可访问内容 | - |
| FE-36 权限-按钮 | `/permission/button` | 点击按钮 | 无权限按钮不可见/禁用 | - |
| FE-37 关于 | `/about` | 打开 | 项目信息正常展示 | - |
| FE-38 引导页 | `/guide` | 打开 | 引导步骤可交互 | - |
| FE-39 空页面 | `/empty` | 打开 | 正常渲染无报错 | - |

### 6.5 前端通用断言（所有页面）

- 页面打开时 Network 无 4xx/5xx（除设计上 401 后自动刷新 token 的场景）；
- Console 无未捕获异常；表格操作（新增/编辑/删除）后列表数据即时刷新；
- 分页器页码/每页数与 `data.total` 一致。

---

## 7. 自动化回归执行方案

### 7.1 后端单元/集成测试

```bash
cd e:\GitHub\Hello-FastApi\service
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/ui_test.py
# 按需：pytest tests/unit/           单元
#      pytest tests/integration/     集成
#      pytest -n auto                并行（xdist，安全）
```

### 7.2 静态检查与类型

```bash
# 后端
ruff check src/ tests/ && ruff format src/ tests/ && mypy src/
# 前端
cd ..\web
npm run typecheck          # vue-tsc --noEmit --skipLibCheck
npm run lint               # ⚠️ 内部调 pnpm；本机可改 .bin 直接跑，见 2.4 注
```

### 7.3 API 冒烟脚本（service/_smoke_api.py）

覆盖：登录 → 9 大模块 CRUD 全链路 → 认证辅助 → 树形/特殊查询 → 日志监控 → 登出。

```bash
cd e:\GitHub\Hello-FastApi\service
# 前置：后端已启动（http://localhost:8000）
.\.venv\Scripts\python.exe _smoke_api.py
```

通过判定：输出中每个模块 `create/list/detail/update/delete` 均为 200/201（menu/dept/dictionary 的 detail 显示「无详情端点」为正常），其余节点全部 200，无堆栈异常。

> ⚠️ 该脚本会向 dev 库写入 `smoke_*`/`reg_*` 前缀的测试数据（每轮时间戳后缀不重复），属预期行为。

### 7.4 前端构建与 E2E

```bash
cd ..\web
npm run build              # 生产构建（vite build）

# Playwright E2E（需后端 + 前端均已启动）
pnpm test:e2e              # 参考 web/e2e/login.spec.ts
```

### 7.5 完整验收流水线

```text
1) service: pytest 全量通过
2) service: ruff check + format + mypy 通过
3) service: python _smoke_api.py 全 2xx
4) web: npm run typecheck 通过
5) web: eslint（--max-warnings 0）通过
6) web: npm run build 成功
7) 前端人工/E2E：登录 → 各页面 CRUD 冒烟
```

---

## 8. 本次验证执行结果（2026-08-21）

| 项目 | 命令/方式 | 结果 |
|---|---|---|
| 后端全量测试 | `pytest -q --ignore=tests/ui_test.py` | ✅ **2143 passed**（1 warning，265.18s） |
| API 全链路冒烟 | `_smoke_api.py` | ✅ 9 模块 CRUD 全 200/201；认证/树形/日志/监控/登出全 200 |
| 前端类型检查 | `npm run typecheck` | ✅ 无错误 |
| 前端 ESLint | `eslint --cache --max-warnings 0 src mock build` | ✅ 0 错误 |
| 前端生产构建 | `vite build` | ✅ 构建成功（dist 输出正常） |
| 前端 Prettier/Stylelint | `prettier --check` / `stylelint` | ⚠️ 存量问题（见 §9.1） |
| 性能优化 | Redis 超时参数化 | ✅ 每请求延迟 12.2s → 3~5s（见 §9.2） |

> 注：本次验证过程输出（pytest 全量日志、冒烟详细输出）为临时产物，已在代码提交前清理；如需复核证据，按 §7 重新执行对应命令即可复现同一结果。

---

## 9. 已知问题与注意事项

### 9.1 前端存量格式问题（不影响功能）

- `prettier --check`：320 个源文件存在格式差异（存量历史代码，本次功能验证不涉及修改）；
- `stylelint`：1855 个错误，其中大量为 `prettier/prettier` 规则与 Prettier 冲突；
- 结论：均为**存量基线问题**，`web/` 在本次会话无源码改动（git status 无 web 变更）。如需全量修复请单独排期，避免产生巨大 diff。

### 9.2 Redis 缺失时的降级表现

- 无 Redis 时每次请求产生约 3 次缓存 socket 超时（读/写 ×2 类操作），
  优化前每请求 12.2~20.4s（默认 4s 超时 × 3）；已新增可配置项
  `REDIS_CONNECT_TIMEOUT` / `REDIS_SOCKET_TIMEOUT`（默认 1.0s），现每请求 3~5s。
- `GET /cache-info` 在 Redis 缺失时返回 `data.connected=false` 的降级响应（HTTP 仍 200）。
- `slowapi` 限流在 Redis 缺失时打印一次内部错误并跳过限流检查（不影响功能，日志噪音）。
- 建议生产环境部署 Redis（`service/docker/docker-compose.yml` 已内置）。

### 9.3 接口存在但易踩的坑（已在 §4/§5 标注）

| 要点 | 说明 |
|---|---|
| 列表接口是 POST | 所有分页列表为 `POST {prefix}`，body 分页参数 |
| 用户创建返回 201 | 其余模块创建返回 200 |
| menu/dept/dictionary 无 GET 详情 | 只有 PUT/DELETE |
| 字典列表 `data` 为裸数组 | 非 `{list:[...]}`，脚本解析需兼容 |
| `/mine` 无 id 字段 | 获取当前用户 id 需从用户列表按 username 匹配 |
| `ruleType` 必须是字符串 | ip-rule 创建时传 `"blacklist"` 而非 1 |
| `list-role-ids` 需 `userId` | `role-menu-ids` 需 `id`（roleId） |
| 登出需 JSON Content-Type | 否则可能 415/422 |
| 冒烟会写测试数据 | `smoke_*` / `reg_*` 前缀，属预期 |

### 9.4 本机工具链注意

- `pnpm` 不在 PATH：用 `corepack.cmd pnpm` 或 `node_modules/.bin/*.cmd` 直接调用；
- pnpm 11 与现有 node_modules 布局不兼容（旧版 pnpm 安装），直接 `pnpm install` 会要求重建依赖（无 TTY 中断），**不建议无事重建**；
- PowerShell 不支持 `&&`，命令用 `;` 分隔。

---

## 10. 附录：API 端点索引（76 个）

> 提取自 `http://localhost:8000/openapi.json`（2026-08-21）。`[鉴权]` 表示需 `Bearer token`。

```
GET   /health                                            [无鉴权]
GET   /api/system/get-async-routes                        [鉴权] 动态路由
GET   /api/system/mine                                    [鉴权] 个人资料
GET   /api/system/mine-logs                               [鉴权] 个人安全日志
POST  /api/system/role-menu                               [鉴权] 菜单权限树
POST  /api/system/role-menu-ids                           [鉴权] 角色菜单id（body: id）
GET   /api/system/list-all-role                           [鉴权] 全部角色
POST  /api/system/list-role-ids                           [鉴权] 用户角色id（body: userId）
POST  /api/system/login                                   [无鉴权]
POST  /api/system/logout                                  [鉴权]
POST  /api/system/refresh-token                           [无鉴权]
POST  /api/system/register                                [无鉴权]
POST  /api/system/user/assign-role                        [鉴权]
POST  /api/system/user/batch-delete                       [鉴权]
POST  /api/system/user/change-password                    [鉴权]
POST  /api/system/user/create                             [鉴权] → 201
DELETE /api/system/user/{user_id}                         [鉴权]
GET   /api/system/user/{user_id}                          [鉴权]
PUT   /api/system/user/{user_id}                          [鉴权]
GET   /api/system/user/info                               [鉴权]
POST  /api/system/user                                    [鉴权] 分页列表
PUT   /api/system/user/{user_id}/reset-password           [鉴权]
PUT   /api/system/user/profile                            [鉴权]
PUT   /api/system/user/{user_id}/status                   [鉴权]
POST  /api/system/user/avatar                             [鉴权] multipart
POST  /api/system/role/{role_id}/menus                    [鉴权]
POST  /api/system/role/{role_id}/data-scope               [鉴权]
POST  /api/system/role/create                             [鉴权]
DELETE /api/system/role/{role_id}                         [鉴权]
GET   /api/system/role/{role_id}                          [鉴权]
PUT   /api/system/role/{role_id}                          [鉴权]
POST  /api/system/role                                    [鉴权] 分页列表
PUT   /api/system/role/{role_id}/status                   [鉴权]
POST  /api/system/menu/create                             [鉴权]
DELETE /api/system/menu/{menu_id}                         [鉴权]
PUT   /api/system/menu/{menu_id}                          [鉴权]
POST  /api/system/menu                                    [鉴权] 分页列表
GET   /api/system/menu/tree                               [鉴权]
GET   /api/system/menu/user-menus                         [鉴权]
POST  /api/system/dept/create                             [鉴权]
DELETE /api/system/dept/{dept_id}                         [鉴权]
PUT   /api/system/dept/{dept_id}                          [鉴权]
POST  /api/system/dept                                    [鉴权] 分页列表
GET   /api/system/dept/tree                               [鉴权]
POST  /api/system/dictionary/create                       [鉴权]
DELETE /api/system/dictionary/{dict_id}                   [鉴权]
PUT   /api/system/dictionary/{dict_id}                    [鉴权]
GET   /api/system/dictionary/type/{dict_name}             [鉴权]
POST  /api/system/dictionary/getByName                    [鉴权]
POST  /api/system/dictionary                              [鉴权] 分页列表（data 裸数组）
POST  /api/system/login-logs/batch-delete                 [鉴权]
POST  /api/system/operation-logs/batch-delete             [鉴权]
POST  /api/system/login-logs/clear                        [鉴权]
POST  /api/system/operation-logs/clear                    [鉴权]
POST  /api/system/login-logs                              [鉴权] 分页列表
POST  /api/system/operation-logs                          [鉴权] 分页列表
POST  /api/system/system-logs-detail                      [鉴权] body: id
POST  /api/system/system-logs                             [鉴权] 分页列表
POST  /api/system/config/create                           [鉴权]
DELETE /api/system/config/{config_id}                     [鉴权]
GET   /api/system/config/{config_id}                      [鉴权]
PUT   /api/system/config/{config_id}                      [鉴权]
POST  /api/system/config                                  [鉴权] 分页列表
POST  /api/system/notice/batch-delete                     [鉴权]
POST  /api/system/notice/create                           [鉴权]
DELETE /api/system/notice/{notice_id}                     [鉴权]
GET   /api/system/notice/{notice_id}                      [鉴权]
PUT   /api/system/notice/{notice_id}                      [鉴权]
GET   /api/system/notice/latest                           [鉴权]
POST  /api/system/notice                                  [鉴权] 分页列表
POST  /api/system/post/batch-delete                       [鉴权]
POST  /api/system/post/create                             [鉴权]
DELETE /api/system/post/{post_id}                         [鉴权]
GET   /api/system/post/{post_id}                          [鉴权]
PUT   /api/system/post/{post_id}                          [鉴权]
POST  /api/system/post                                    [鉴权] 分页列表
GET   /api/system/post/options                            [鉴权]
GET   /api/system/post/user/{user_id}                     [鉴权]
POST  /api/system/online-logs/force-offline               [鉴权] body: id
GET   /api/system/cache-info                              [鉴权]
POST  /api/system/get-card-list                           [鉴权]
GET   /api/system/get-map-info                            [鉴权]
POST  /api/system/online-logs                             [鉴权] 分页列表
GET   /api/system/server-info                             [鉴权]
POST  /api/system/ip-rule/batch-delete                    [鉴权]
POST  /api/system/ip-rule/clear                           [鉴权]
POST  /api/system/ip-rule/create                          [鉴权]
DELETE /api/system/ip-rule/{rule_id}                      [鉴权]
GET   /api/system/ip-rule/{rule_id}                       [鉴权]
PUT   /api/system/ip-rule/{rule_id}                       [鉴权]
POST  /api/system/ip-rule                                 [鉴权] 分页列表
```

---

## 执行检查单（给 Agent）

```text
□ 环境：后端 8000 可访问（GET /health 200）；前端 8848 可访问
□ 认证：POST /login 获取 token 成功（AUTH-01）
□ 后端：pytest 全量通过（AC-1）；冒烟脚本全 2xx（AC-2）
□ 后端静态：ruff / mypy 通过
□ 前端：typecheck（AC-3）/ eslint（AC-4）/ build（AC-5）通过
□ 功能：按 §5 模块用例逐条核对；按 §6 页面用例打开各页面操作一遍（AC-6）
□ 收尾：恢复测试改动（如 admin 密码若被改）、清理多余测试数据（可选）
□ 结论：所有满足得「通过」，否则记录失败用例编号与原因
```