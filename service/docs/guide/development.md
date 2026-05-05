# 开发规范

本文档定义了项目的代码风格、数据库规范和代码检查规则，确保代码质量和团队协作一致性。

[← 返回首页](../../README.md)

---

## 代码风格

### 基本原则

- 遵循 **PEP 8** 规范
- **所有代码注释使用中文描述**
- 所有公共接口使用类型提示（Type Hints）
- 行长度上限：320 字符（Ruff 配置）

### Ruff 配置

项目使用 Ruff 进行代码格式化和静态检查，配置位于 `pyproject.toml`：

```toml
[tool.ruff]
line-length = 320
```

### 导入顺序

Ruff 自动管理导入顺序（`isort` 规则），按以下分组：

1. 标准库
2. 第三方库
3. 项目内部模块

---

## 数据库规范

### 表名规范

- 所有数据表以 `sys_` 为前缀，例如：`sys_users`、`sys_roles`
- 表名使用小写蛇形命名法（snake_case）

### 主键规范

- `id` 字段使用 36 位 UUID 字符串
- 由应用层生成，不依赖数据库自增

### 关键数据表

| 表名 | 说明 |
|------|------|
| `sys_users` | 用户表 |
| `sys_roles` | 角色表 |
| `sys_menus` | 菜单表 |
| `sys_permissions` | 权限表 |
| `sys_departments` | 部门表 |
| `sys_user_roles` | 用户-角色关联表 |
| `sys_role_menus` | 角色-菜单关联表 |
| `sys_login_logs` | 登录日志表 |
| `sys_operation_logs` | 操作日志表 |
| `sys_ip_rules` | IP 访问规则表 |
| `sys_system_config` | 系统配置表 |

### ORM 模型

数据库模型定义在 `src/infrastructure/database/models/` 目录下，使用 SQLModel 定义。每个模型对应一张数据库表，字段使用中文注释说明。

---

## 代码检查

### Ruff 检查与格式化

```bash
# 代码检查（自动修复）
ruff check . --fix

# 代码格式化
ruff format .
```

Ruff 集成了 flake8、isort 等工具的功能，替代了传统的多个 Linter 工具。

### MyPy 类型检查

```bash
# 对 src 目录进行类型检查
mypy src/
```

MyPy 会检查类型注解的正确性，发现潜在的类型错误。

### 完整检查流程

建议在提交代码前执行以下完整检查：

```bash
# 1. Ruff 检查 + 自动修复
ruff check . --fix

# 2. Ruff 格式化
ruff format .

# 3. MyPy 类型检查
mypy src/

# 4. 运行测试
pytest

# 5. 测试覆盖率检查
pytest --cov=src --cov-report=term-missing
```

---

## DDD 分层规范

项目采用 DDD（领域驱动设计）四层架构，详细的分层约束请参阅 [项目架构设计与约束](../design/项目架构设计与约束.md)。

### 核心原则

- **依赖方向始终向内**：领域层不依赖任何外层
- **基础设施层实现领域层定义的抽象接口**（依赖倒置）
- **接口层不包含业务逻辑**，仅做请求校验、DTO 转换
- **事务在应用层控制**，领域层不处理事务

### 各层职责简述

| 层 | 目录 | 职责 |
|----|------|------|
| 接口层 | `src/api/` | HTTP 请求处理、认证授权、依赖注入 |
| 应用层 | `src/application/` | 用例编排、DTO 定义、事务边界 |
| 领域层 | `src/domain/` | 核心业务逻辑、实体、仓储接口 |
| 基础设施层 | `src/infrastructure/` | 仓储实现、ORM 模型、缓存、配置 |

---

## API 响应格式

所有接口返回统一的响应结构：

### 普通响应

```json
{
  "code": 0,
  "message": "操作成功",
  "data": {}
}
```

### 分页响应

```json
{
  "code": 0,
  "message": "操作成功",
  "data": {
    "list": [],
    "total": 0,
    "pageSize": 10,
    "currentPage": 1
  }
}
```

| 字段 | 说明 |
|------|------|
| `code` | 状态码，0 表示成功 |
| `message` | 提示信息 |
| `data` | 业务数据 |
| `data.list` | 分页数据列表 |
| `data.total` | 总记录数 |
| `data.pageSize` | 每页大小 |
| `data.currentPage` | 当前页码 |
