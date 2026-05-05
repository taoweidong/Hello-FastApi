# 管理命令

项目通过 `python -m scripts.cli` 提供一系列管理命令，用于数据库初始化、数据填充和服务器管理等操作。

[← 返回首页](../../README.md)

---

## 命令总览

| 命令 | 说明 |
|------|------|
| `runserver` | 启动开发服务器（默认端口 8000） |
| `initdb` | 初始化数据库表 |
| `seedrbac` | 初始化默认角色和权限数据 |
| `seeddata` | 初始化测试数据（菜单、登录日志、操作日志、系统日志） |
| `createsuperuser` | 创建超级管理员 |

---

## runserver

启动开发服务器，默认监听 `0.0.0.0:8000`。

```bash
python -m scripts.cli runserver
```

启动后可访问：
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

---

## initdb

创建所有数据库表，基于 `src/infrastructure/database/models/` 中定义的 SQLModel 模型自动建表。

```bash
python -m scripts.cli initdb
```

> **注意**：此命令只会创建不存在的表，不会删除或修改已有的表结构。如需重建，请先删除数据库文件。

---

## seedrbac

初始化 RBAC（基于角色的访问控制）基础数据，包括：

- 默认角色（admin、user、moderator）
- 为 admin 角色分配所有菜单权限（确保超级管理员拥有完整权限）

```bash
python -m scripts.cli seedrbac
```

> **注意**：必须在 `initdb` 和 `seeddata` 之后执行，因为菜单权限分配依赖菜单数据。

---

## seeddata

初始化测试数据，用于开发和演示，包括：

- 系统菜单（对应前端路由）
- 登录日志示例
- 操作日志示例
- 系统日志示例

```bash
python -m scripts.cli seeddata
```

> **注意**：必须在 `seedrbac` 之后执行，因为菜单数据依赖角色关联。

---

## createsuperuser

创建超级管理员账户。超级用户拥有以下权限：

- `is_superuser=1`：自动绕过所有权限检查
- 自动分配 **admin 角色**：拥有所有菜单权限
- 登录时自动获取全部菜单和路由

### 完整参数

```bash
python -m scripts.cli createsuperuser --username <用户名> --email <邮箱> --password <密码> [--nickname <昵称>]
```

### 简写形式

```bash
python -m scripts.cli createsuperuser -u <用户名> -e <邮箱> -p <密码> [-n <昵称>]
```

### 参数说明

| 参数 | 简写 | 必填 | 说明 |
|------|------|------|------|
| `--username` | `-u` | 是 | 登录用户名，唯一 |
| `--email` | `-e` | 是 | 邮箱地址，唯一 |
| `--password` | `-p` | 是 | 登录密码 |
| `--nickname` | `-n` | 否 | 显示昵称，默认同用户名 |

### 示例

```bash
# 创建管理员
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123

# 创建带昵称的管理员
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123 -n 系统管理员
```

---

## 初始化顺序

完整的数据库初始化应按以下顺序执行：

```bash
# 1. 创建数据库表
python -m scripts.cli initdb

# 2. 初始化测试数据（菜单、日志等）
python -m scripts.cli seeddata

# 3. 初始化 RBAC 数据（角色、菜单权限分配）
python -m scripts.cli seedrbac

# 4. 创建超级管理员（自动分配 admin 角色）
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
```
