# RBAC 与数据权限

> 本系统的权限模型：**菜单即权限**。目录/页面控制"能看到哪"，按钮（PERMISSION 节点）
> 控制"能点哪个"，数据权限控制"能看到哪些行的数据"。

[← 返回文档导航](../README.md)

---

## 1. 三类菜单节点

| menu_type | 含义 | 作用 |
|---|---|---|
| 0 DIRECTORY | 目录 | 路由分组（含子菜单） |
| 1 MENU | 页面 | 一条动态路由（component 指向前端页面） |
| 2 PERMISSION | 按钮 | 一个权限码（`name` 字段即码值，如 `user:add`） |

- 登录后前端调用 `GET /get-async-routes` 拿到路由树：
  - 仅含 DIRECTORY/MENU 节点；
  - 每个节点的 `meta.auths` 汇总了它下面（及祖先传播下来的）权限码列表；
  - 前端 `v-auth="'user:add'"` 指令据此控制按钮显隐。
- 后端二次校验：路由依赖 `require_permission("user:add")`（缓存优先，超管快捷放行）。

## 2. 超级管理员

- `is_superuser=1` 的用户跳过所有权限码校验，动态路由返回全量菜单；
- 普通用户按其角色的菜单并集返回（`get_user_all_menus`）。

## 3. 数据权限（DataScope 五档）

角色维度配置，决定用户列表等接口能看到的数据范围：

| 值 | 档位 | 可见范围 |
|---|---|---|
| 1 | ALL | 全部数据 |
| 2 | CUSTOM | 自定义部门集合（role_dept_link） |
| 3 | DEPT | 本部门 |
| 4 | DEPT_AND_CHILD | 本部门及子部门（部门树 BFS） |
| 5 | SELF | 仅本人 |

- 配置入口：角色管理页「数据权限」抽屉（`POST /role/{id}/data-scope`，
  保存 dataScope + 重建部门关联）；
- 解析逻辑：`UserService._resolve_data_scope` → 仓储 `scope_dept_ids/scope_user_id` 过滤；
- 性能注意：DEPT_AND_CHILD 每请求做部门树 BFS（当前量级可接受，见优化报告遗留项）。

## 4. 令牌与权限缓存的一致性

| 操作 | 缓存动作 | 生效时延 |
|---|---|---|
| 角色分配菜单 / 修改数据权限 / 启停 / 删除 | 批量失效该角色下所有用户的 user:info + user:perms | 立即 |
| 用户被改密 / 改角色 / 删除 | 失效该用户缓存 | 立即 |
| 未主动失效 | TTL 300s 到期回源 | ≤5 分钟 |

> 历史教训：角色侧变更曾不失效缓存，造成最长 5 分钟越权窗口——现已批量失效
> （`role_service._invalidate_role_users_cache`）。

## 5. 二次开发：新增一个权限码

1. 菜单管理页（或 `rbac_defaults.py` 种子）在目标页面节点下新增
   `menu_type=2` 子节点，`name=你的权限码`（如 `export:user`）；
2. 前端按钮加 `v-auth="'export:user'"`；
3. 后端路由依赖加 `require_permission("export:user")`；
4. 给需要的角色在角色管理页勾选该按钮节点；
5. 该角色用户重新登录（或等待缓存失效）后生效。

完整开发流程见[后端 CRUD 开发指南](../development/backend-crud-guide.md)。
