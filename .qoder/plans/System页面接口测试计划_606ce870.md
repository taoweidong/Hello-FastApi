# System 页面接口测试计划

## 概述
测试 `web\src\views\system` 下的四个管理页面（用户、角色、菜单、部门），验证前后端接口连通性和页面功能正常。

---

## 任务 1: 启动后端服务
- **目录**: `e:\GitHub\Hello-FastApi\service`
- **命令**: `fastapi dev src/main.py` 或 `uvicorn src.main:app --reload --port 8000`
- **端口**: 8000
- **验证**: 访问 http://localhost:8000/docs 确认 API 文档正常加载

## 任务 2: 启动前端服务
- **目录**: `e:\GitHub\Hello-FastApi\web`
- **命令**: `pnpm dev`
- **端口**: 8848
- **代理配置**: `/api` -> `http://localhost:8000`
- **验证**: 访问 http://localhost:8848 确认页面正常加载

## 任务 3: 用户管理页面测试
**路径**: `/system/user`
**API 接口**:
| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 用户列表 | POST | `/api/system/user` | 分页查询用户 |
| 创建用户 | POST | `/api/system/user/create` | 新增用户 |
| 更新用户 | PUT | `/api/system/user/{id}` | 修改用户信息 |
| 删除用户 | DELETE | `/api/system/user/{id}` | 删除单个用户 |
| 批量删除 | POST | `/api/system/user/batch-delete` | 批量删除用户 |
| 重置密码 | PUT | `/api/system/user/{id}/reset-password` | 重置用户密码 |
| 修改状态 | PUT | `/api/system/user/{id}/status` | 启用/禁用用户 |
| 分配角色 | POST | `/api/system/user/assign-role` | 为用户分配角色 |

**测试要点**:
- 列表加载、分页、筛选功能
- 新增/编辑表单提交
- 删除确认弹窗
- 批量操作功能
- 部门树筛选

## 任务 4: 角色管理页面测试
**路径**: `/system/role`
**API 接口**:
| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 角色列表 | POST | `/api/system/role` | 分页查询角色 |
| 创建角色 | POST | `/api/system/role/create` | 新增角色 |
| 更新角色 | PUT | `/api/system/role/{id}` | 修改角色信息 |
| 删除角色 | DELETE | `/api/system/role/{id}` | 删除角色 |
| 菜单权限 | POST | `/api/system/role/{id}/menu` | 分配菜单权限 |

**测试要点**:
- 列表加载、分页、筛选功能
- 新增/编辑角色
- 删除角色
- 菜单权限树展示与保存

## 任务 5: 菜单管理页面测试
**路径**: `/system/menu`
**API 接口**:
| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 菜单列表 | POST | `/api/system/menu` | 获取菜单树 |
| 创建菜单 | POST | `/api/system/menu/create` | 新增菜单 |
| 更新菜单 | PUT | `/api/system/menu/{id}` | 修改菜单 |
| 删除菜单 | DELETE | `/api/system/menu/{id}` | 删除菜单 |

**测试要点**:
- 菜单树形表格展示
- 新增/编辑菜单（支持层级）
- 删除菜单（级联删除子菜单）

## 任务 6: 部门管理页面测试
**路径**: `/system/dept`
**API 接口**:
| 接口 | 方法 | 路径 | 功能 |
|------|------|------|------|
| 部门列表 | POST | `/api/system/dept` | 获取部门树 |
| 创建部门 | POST | `/api/system/dept/create` | 新增部门 |
| 更新部门 | PUT | `/api/system/dept/{id}` | 修改部门 |
| 删除部门 | DELETE | `/api/system/dept/{id}` | 删除部门 |

**测试要点**:
- 部门树形表格展示
- 新增/编辑部门（支持层级）
- 删除部门

---

## 任务 7: 提交并推送代码
如果测试过程中发现问题并修复，或数据有更新：
- `git add .`
- `git commit -m "test: 验证 system 页面接口功能"`
- `git push origin master`

---

## 注意事项
1. 测试前确保数据库 `service/sql/dev.db` 存在且有初始数据
2. 需要登录后才能访问 system 页面，使用 admin 账户登录
3. 部分接口需要特定权限，确保测试账户有对应权限
4. 测试过程中如发现 Bug，记录问题并修复后重新测试