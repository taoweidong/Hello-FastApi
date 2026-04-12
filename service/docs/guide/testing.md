# 测试

本文档介绍项目的测试策略、测试命令和覆盖率配置。

[← 返回首页](../../README.md)

---

## 测试策略

项目按照 DDD 分层架构采用不同的测试策略：

| 层级 | 测试类型 | 说明 |
|------|----------|------|
| 领域层 | 纯单元测试 | 不依赖数据库、网络等外部资源，直接测试实体、值对象、领域服务 |
| 应用层 | 单元测试 | 模拟仓储和领域服务，验证用例编排逻辑 |
| 基础设施层 | 集成测试 | 使用真实数据库验证仓储实现 |
| 接口层 | 端到端测试 | 通过 FastAPI TestClient 验证 API 行为 |

---

## 测试目录结构

```
tests/
├── conftest.py          # 公共 fixture 定义
├── unit/                # 单元测试
│   ├── test_auth.py     # 认证相关单元测试
│   ├── test_dto_validators.py  # DTO 验证器测试
│   └── ...
└── integration/         # 集成测试
    └── ...
```

- `unit/`：单元测试，不依赖外部服务，快速执行
- `integration/`：集成测试，需要数据库等外部依赖，验证完整流程

---

## 运行测试

### 运行所有测试

```bash
cd service
pytest
```

### 运行指定类型的测试

```bash
# 仅运行单元测试
pytest tests/unit/

# 仅运行集成测试
pytest tests/integration/
```

### 运行指定测试文件

```bash
pytest tests/unit/test_auth.py
```

### 运行指定测试用例

```bash
pytest tests/unit/test_auth.py::test_login
```

---

## 测试覆盖率

### 生成覆盖率报告

```bash
# 终端输出覆盖率
pytest --cov=src --cov-report=term-missing

# 生成 HTML 覆盖率报告
pytest --cov=src --cov-report=html
```

HTML 报告生成在 `htmlcov/` 目录下，用浏览器打开 `htmlcov/index.html` 即可查看。

### 覆盖率配置

覆盖率配置位于 `pyproject.toml`：

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.coverage.run]
source = ["src"]
```

---

## 测试环境配置

测试环境使用独立的配置文件 `.env.testing`，关键配置：

- 使用 SQLite 内存数据库（`sqlite+aiosqlite://`），测试完成后自动清理
- 不连接真实 Redis，使用模拟缓存
- DEBUG 模式开启

测试环境通过 `APP_ENV=testing` 自动激活，`conftest.py` 中已配置自动切换。

---

## 编写测试

### 单元测试示例

```python
import pytest
from src.application.dto.user_dto import CreateUserDTO


def test_create_user_dto_validation():
    """测试创建用户 DTO 的字段验证"""
    dto = CreateUserDTO(
        username="testuser",
        email="test@example.com",
        password="Test123456",
    )
    assert dto.username == "testuser"
    assert dto.email == "test@example.com"
```

### 集成测试示例

```python
import pytest
from httpx import AsyncClient
from src.config.asgi import create_app


@pytest.mark.asyncio
async def test_login_api():
    """测试登录 API"""
    app = create_app()
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/system/login",
            json={"username": "admin", "password": "admin123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
```

### Fixture 使用

`conftest.py` 中定义了常用的 fixture：

- `db_session`：测试数据库会话
- `client`：FastAPI TestClient 实例
- `test_user`：测试用户数据

可在测试文件中直接通过参数注入使用。

---

## 常见问题

### 测试数据库残留

如果测试中途失败导致数据库未清理，删除 `sql/` 目录下的测试数据库文件即可。

### 异步测试

项目使用 `pytest-asyncio` 支持异步测试。异步测试函数需要添加 `@pytest.mark.asyncio` 装饰器。
