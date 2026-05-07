# Service 代码质量优化设计文档

## 概述

对 Hello-FastApi service 层进行渐进式质量优化，分 4 个阶段执行，每阶段独立验证。

## 当前质量状况

| 指标 | 现状 | 目标 |
|------|------|------|
| ruff check src/ | ✅ 0 errors | 保持 |
| ruff check tests/ | ❌ 157 errors | ✅ 0 errors |
| mypy src/ | ✅ 通过（配置宽松）| 逐步收紧 |
| API 路由测试覆盖 | 0% | 后续阶段补全 |

## 阶段 1：修复测试 Lint 错误

### 1.1 删除重复测试函数
- **文件**: `tests/unit/application/services/test_log_service.py`
- **操作**: 删除重复定义的 `test_get_login_logs_with_time_range`

### 1.2 清理未使用导入
- `AsyncMock`（未使用的 test 文件）
- `RateLimitExceeded`（未使用的 test 文件）
- 其他 F401 违规

### 1.3 清理未使用变量
- `mgr`, `result` → 移除或加 `_` 前缀

### 1.4 修复 lambda 循环变量捕获
- `lambda x: func(i, x)` → `lambda x, i=i: func(i, x)`

### 1.5 修复泛型异常断言
- `with pytest.raises(Exception)` → 使用具体异常类型

### 1.6 行长度 & import 排序
- 超长行拆分到 120 字符以内
- 修正 import 排序

## 阶段 2：提取重复代码

### 2.1 菜单序列化工具
- **新建**: `src/application/utils/menu_mapper.py`
- **提取**: `MenuService` 和 `AuthService` 中相同的 entity↔dict 转换逻辑
- **影响**: 两个服务改为调用公共 mapper

### 2.2 日志响应格式化
- **文件**: `src/api/v1/log_router.py`
- **提取**: 三个日志端点的 entity→dict 循环为 `_format_log_response(entities)`

## 阶段 3：迁移 auth_router 业务逻辑到 AuthService

### 3.1 AuthService 新增方法
- `get_user_async_routes(user_id: str) -> list[dict]`
- `get_role_menu_ids(role_id: str) -> list[str]`
- `get_role_ids(user_id: str) -> list[str]`

### 3.2 auth_router.py 简化
- 移除 `_build_route_tree`, `_build_meta` 等私有方法
- 端点改为调用 AuthService 对应方法

## 阶段 4：补全类型提示

### 4.1 API 依赖层
- `require_permission` → 补充返回类型
- `require_menu_permission` → 补充返回类型
- `require_superuser` → 补充返回类型

### 4.2 Service 层
- `AuthService._build_meta(menu: MenuEntity) -> dict`

## 验证流程

每阶段完成后执行对应验证：
- 阶段 1: `ruff check tests/`
- 阶段 2: `ruff check src/ && pytest`
- 阶段 3: `pytest`
- 阶段 4: `mypy src/`
