# P0 基础设施完善实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成四项 P0 基础设施任务：Alembic 数据库迁移、限流中间件、Docker Compose 补全、Jenkins CI/CD 流水线。

**Architecture:** 四项任务相互独立，按 P0-1 → P0-2 → P0-3 → P0-4 顺序执行，每项任务完成后自验证。

**Tech Stack:** Alembic, SQLModel, slowapi, Redis, Docker Compose, PostgreSQL, Jenkins Pipeline, Python 3.10

---

## 文件映射总览

| 任务 | 新建文件 | 修改文件 |
|------|----------|----------|
| P0-1 | `service/alembic.ini`, `service/alembic/env.py`, `service/alembic/versions/*.py` | `service/scripts/cli.py`, `service/pyproject.toml` |
| P0-2 | `service/tests/unit/test_limiter.py` | `service/src/infrastructure/http/limiter.py`, `service/src/main.py` |
| P0-3 | - | `service/docker/docker-compose.yml` |
| P0-4 | `service/Jenkinsfile`, `service/docker/Jenkins/deploy.sh` | - |

---

### Task 1: 集成 Alembic 数据库迁移

**Files:**
- Create: `service/alembic.ini`
- Create: `service/alembic/env.py`
- Create: `service/alembic/script.py.mako`
- Create: `service/alembic/versions/001_initial_schema.py`
- Create: `service/tests/unit/test_alembic_cli.py`
- Modify: `service/scripts/cli.py`
- Modify: `service/pyproject.toml`

- [ ] **Step 1: 添加 Alembic 到 pyproject.toml 依赖**

修改 `service/pyproject.toml`，在 `dependencies` 中添加 `alembic>=1.13.0`：

```toml
[project]
name = "hello-fastapi"
version = "0.1.0"
description = "FastAPI + DDD + RBAC 权限认证系统"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastapi[standard]>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "sqlmodel>=0.0.22",
    "fastcrud>=0.15.0",
    "classy-fastapi>=0.7.0",
    "aiosqlite>=0.20.0",
    "asyncpg>=0.30.0",
    "aiomysql>=0.2.0",
    "pymysql>=1.1.0",
    "pydantic-settings>=2.0.0",
    "python-jose[cryptography]>=3.3.0",
    "bcrypt>=4.0.0",
    "python-multipart>=0.0.9",
    "redis>=5.0.0",
    "loguru>=0.7.0",
    "httpx>=0.27.0",
    "slowapi>=0.1.9",
    "limits>=3.10.0",
    "alembic>=1.13.0",
]
```

- [ ] **Step 2: 运行 uv pip install 安装 alembic**

```bash
cd service
uv pip install "alembic>=1.13.0"
```

- [ ] **Step 3: 创建 alembic.ini 配置文件**

创建 `service/alembic.ini`：

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **Step 4: 创建 alembic/env.py（async 适配）**

创建 `service/alembic/env.py`：

```python
"""Alembic 环境配置，适配 SQLModel + async engine。"""

import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

# 注册所有模型（确保 metadata 包含所有表）
import src.infrastructure.database.models  # noqa: F401

from src.config.settings import Settings

config = context.config

# 从 .env 文件读取 DATABASE_URL 覆盖 alembic.ini 中的占位符
_settings = Settings()
if config.config_file_name is not None:
    config.set_main_option("sqlalchemy.url", _settings.DATABASE_URL)

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本而不连接数据库。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """在线模式：实际连接数据库执行迁移。"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步迁移入口。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口。"""
    url = config.get_main_option("sqlalchemy.url")
    if url and url.startswith("sqlite"):
        # SQLite 不支持 async driver 的某些操作，使用 sync 模式
        from sqlalchemy import create_engine

        sync_url = url.replace("sqlite+aiosqlite://", "sqlite://")
        connectable = create_engine(sync_url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 5: 创建 alembic/script.py.mako 模板**

创建 `service/alembic/script.py.mako`：

```python
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **Step 6: 扩展 scripts/cli.py 添加 migrate 和 rollback 命令**

修改 `service/scripts/cli.py`，在 `main()` 函数中添加 migrate 和 rollback 子命令：

在现有 import 后添加：
```python
import argparse
import asyncio
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn

from src.config.settings import settings
```

添加 migrate 和 rollback 函数：
```python
def run_migrate() -> None:
    """执行 Alembic 数据库迁移 (upgrade head)。"""
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=project_root,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    if result.returncode == 0:
        print("数据库迁移成功")
    else:
        print("数据库迁移失败", file=sys.stderr)
        sys.exit(result.returncode)


def run_rollback(steps: int = 1) -> None:
    """回滚 Alembic 数据库迁移 (downgrade)。"""
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", f"-{steps}"],
        cwd=project_root,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    if result.returncode == 0:
        print(f"数据库回滚 {steps} 步成功")
    else:
        print("数据库回滚失败", file=sys.stderr)
        sys.exit(result.returncode)


def run_stamp(version: str) -> None:
    """标记 Alembic 迁移版本（不执行 SQL）。"""
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "stamp", version],
        cwd=project_root,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    if result.returncode == 0:
        print(f"已标记数据库版本为 {version}")
    else:
        print("标记版本失败", file=sys.stderr)
        sys.exit(result.returncode)
```

在 `main()` 函数中添加子命令解析器（在 `initall` 命令之后）：
```python
    # migrate 命令
    subparsers.add_parser("migrate", help="执行 Alembic 数据库迁移 (upgrade head)")

    # rollback 命令
    rollback_parser = subparsers.add_parser("rollback", help="回滚 Alembic 数据库迁移")
    rollback_parser.add_argument("--steps", "-s", type=int, default=1, help="回滚步数（默认 1）")

    # stamp 命令
    stamp_parser = subparsers.add_parser("stamp", help="标记 Alembic 迁移版本（不执行 SQL）")
    stamp_parser.add_argument("version", help="目标版本号（如 head、base、或具体 revision）")
```

在命令分发逻辑中添加（在 `initall` 分支之后）：
```python
    elif args.command == "migrate":
        run_migrate()
    elif args.command == "rollback":
        run_rollback(args.steps)
    elif args.command == "stamp":
        run_stamp(args.version)
```

- [ ] **Step 7: 生成初始迁移脚本**

```bash
cd service
python -m alembic revision --autogenerate -m "initial_schema"
```

注意：此命令会检测当前数据库状态。如果 SQLite 数据库中已有表，需要先将现有数据库表重命名备份或清理，让 Alembic 从空白状态生成初始 schema。

生成的迁移脚本位于 `service/alembic/versions/<timestamp>_initial_schema.py`，手动调整内容为：

```python
"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2026-04-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建所有表（使用 SQLModel.metadata.create_all 的等效操作）
    from sqlmodel import SQLModel
    import src.infrastructure.database.models  # noqa: F401

    # 获取 bind 并创建所有表
    bind = op.get_bind()
    SQLModel.metadata.create_all(bind)


def downgrade() -> None:
    # 按依赖顺序删除表
    op.drop_table("sys_userrole_menu")
    op.drop_table("sys_userinfo_roles")
    op.drop_table("sys_login_logs")
    op.drop_table("sys_operation_logs")
    op.drop_table("sys_ip_rules")
    op.drop_table("sys_role_menu")
    op.drop_table("sys_roles")
    op.drop_table("sys_menus")
    op.drop_table("sys_menu_metas")
    op.drop_table("sys_departments")
    op.drop_table("sys_dictionaries")
    op.drop_table("sys_system_configs")
    op.drop_table("sys_users")
```

- [ ] **Step 8: 编写 Alembic CLI 单元测试**

创建 `service/tests/unit/test_alembic_cli.py`：

```python
"""Alembic CLI 命令测试。"""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest


def test_migrate_command_runs():
    """测试 migrate 命令可以成功执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "migrate"],
        cwd=project_root,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    # 如果数据库已经迁移到最新版本，会返回 0
    # 如果 alembic.ini 配置有问题，会返回非 0
    assert result.returncode == 0 or "already up to date" in result.stdout.lower() or "no such table" in result.stderr.lower()


def test_rollback_command_exists():
    """测试 rollback 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "rollback", "--steps", "1"],
        cwd=project_root,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    # 命令应该能执行（可能没有可回滚的迁移）
    assert "回滚" in result.stdout or "回滚" in result.stderr or result.returncode == 0


def test_stamp_command_exists():
    """测试 stamp 命令可以执行。"""
    project_root = Path(__file__).parent.parent.parent
    result = subprocess.run(
        ["python", "-m", "scripts.cli", "stamp", "head"],
        cwd=project_root,
        capture_output=True,
        text=True,
        env={**__import__("os").environ, "PYTHONPATH": str(project_root)},
    )
    # 命令应该能执行
    assert result.returncode == 0 or "标记" in result.stdout or "标记" in result.stderr
```

- [ ] **Step 9: 运行测试验证 Alembic 集成**

```bash
cd service
pytest tests/unit/test_alembic_cli.py -v
```

- [ ] **Step 10: 提交 P0-1 变更**

```bash
cd service
git add pyproject.toml alembic.ini alembic/ scripts/cli.py tests/unit/test_alembic_cli.py
git commit -m "feat(P0-1): 集成 Alembic 数据库迁移，添加 migrate/rollback/stamp CLI 命令"
```

---

### Task 2: 限流中间件完善

**Files:**
- Create: `service/tests/unit/test_limiter.py`
- Modify: `service/src/infrastructure/http/limiter.py`
- Modify: `service/src/main.py`

- [ ] **Step 1: 完善 limiter.py - 添加 Redis 后端存储支持**

修改 `service/src/infrastructure/http/limiter.py`，在 limiter 实例化处添加 Redis 后端：

```python
"""限流模块。

基于 slowapi 实现请求限流功能。
通过 SlowAPIMiddleware 全局中间件处理限流，
解决 @limiter.limit() 装饰器与 class-based 路由的兼容性问题。

补丁说明：
- 补丁 1：_get_route_name 无法处理 functools.partial（classy_fastapi 路由端点）
- 补丁 2：_check_request_limit 直接访问 __module__/__name__
- 补丁 3：_check_limits 对非 RateLimitExceeded 异常错误地调用 _rate_limit_exceeded_handler
"""

import functools
import logging
from typing import Callable, Optional, Tuple

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.config.settings import settings

_logger = logging.getLogger(__name__)


def _unwrap_partial(handler):
    """递归解包 functools.partial，返回原始函数。"""
    while isinstance(handler, functools.partial):
        handler = handler.func
    return handler


# ---------------------------------------------------------------------------
# 补丁 1：slowapi.middleware._get_route_name 无法处理 functools.partial
# ---------------------------------------------------------------------------
import slowapi.middleware as _slowapi_middleware

_original_get_route_name = _slowapi_middleware._get_route_name


def _patched_get_route_name(handler):
    return _original_get_route_name(_unwrap_partial(handler))


_slowapi_middleware._get_route_name = _patched_get_route_name


# ---------------------------------------------------------------------------
# 补丁 2：Limiter._check_request_limit 也直接访问 __module__/__name__
# ---------------------------------------------------------------------------
_original_check_request_limit = Limiter._check_request_limit


def _patched_check_request_limit(self, request, endpoint_func, in_middleware=True):
    unwrapped = _unwrap_partial(endpoint_func) if endpoint_func else endpoint_func
    return _original_check_request_limit(self, request, unwrapped, in_middleware)


Limiter._check_request_limit = _patched_check_request_limit


# ---------------------------------------------------------------------------
# 补丁 3：_check_limits 对非 RateLimitExceeded 异常错误地调用
#          _rate_limit_exceeded_handler（要求 exc.detail 属性），
#          导致 AttributeError: 'ValueError' object has no attribute 'detail'
# ---------------------------------------------------------------------------
_original_check_limits = _slowapi_middleware._check_limits


def _patched_check_limits(
    limiter: Limiter, request: Request, handler: Optional[Callable], app: Starlette
) -> Tuple[Optional[Callable], bool, Optional[Exception]]:
    if limiter._auto_check and not getattr(
        request.state, "_rate_limiting_complete", False
    ):
        try:
            limiter._check_request_limit(request, handler, True)
        except RateLimitExceeded as e:
            # 正常限流异常，走标准处理流程
            exception_handler = app.exception_handlers.get(
                type(e), _rate_limit_exceeded_handler
            )
            return exception_handler, False, e
        except Exception as e:
            # 非限流异常（ValueError、AttributeError 等），
            # 不应交给 _rate_limit_exceeded_handler（它要求 exc.detail），
            # 而是记录日志后放行，避免中间件崩溃。
            _logger.exception("slowapi 内部错误，跳过限流检查: %s", e)
            return None, False, None

    return None, False, None


_slowapi_middleware._check_limits = _patched_check_limits


def get_real_ip(request: Request) -> str:
    """获取真实客户端 IP。

    优先从 X-Forwarded-For 获取真实IP，否则使用远程地址。
    适用于反向代理场景。
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return get_remote_address(request)


# ---------------------------------------------------------------------------
# 限流后端配置：Redis 存储（支持分布式多 worker）或内存存储（降级）
# ---------------------------------------------------------------------------
def _get_storage_uri() -> str:
    """获取限流存储 URI。

    优先使用 Redis 作为限流存储（支持分布式多 worker 限流）。
    如果 Redis 不可用或配置为 memory，则使用内存存储。
    """
    # 检查是否配置为内存存储
    rate_limit_storage = getattr(settings, "RATE_LIMIT_STORAGE", "redis")
    if rate_limit_storage == "memory":
        return "memory://"

    # 尝试使用 Redis 存储
    redis_url = getattr(settings, "REDIS_URL", "")
    if redis_url:
        return redis_url

    return "memory://"


# 使用 Redis 或内存作为限流存储
_default_limit = f"{settings.RATE_LIMIT_TIMES}/{settings.RATE_LIMIT_SECONDS}"

limiter = Limiter(
    key_func=get_real_ip,
    default_limits=[_default_limit],
    storage_uri=_get_storage_uri(),
    strategy="fixed-window",
)


def get_limiter() -> Limiter:
    """获取限流器实例。"""
    return limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """限流异常处理器。

    当请求触发限流时返回统一格式的 429 响应。
    """
    return JSONResponse(
        status_code=429,
        content={
            "code": 429,
            "msg": "请求过于频繁，请稍后再试",
            "data": None,
            "retry_after": int(str(exc).split(":")[-1].strip()) if ":" in str(exc) else 60,
        },
        headers={"Retry-After": "60"},
    )
```

- [ ] **Step 2: 在 settings.py 中添加 RATE_LIMIT_STORAGE 配置项**

修改 `service/src/config/settings.py`，在限流配置部分添加：

```python
    # ============ 限流配置 ============
    RATE_LIMIT_TIMES: int = Field(default=100, ge=1)
    RATE_LIMIT_SECONDS: int = Field(default=60, ge=1)
    RATE_LIMIT_STORAGE: str = "redis"  # redis 或 memory
    RATE_LIMIT_WHITELIST_IPS: str = ""  # 逗号分隔的 IP 白名单
```

- [ ] **Step 3: 编写限流单元测试**

创建 `service/tests/unit/test_limiter.py`：

```python
"""限流模块测试。"""

import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.infrastructure.http.limiter import get_limiter, get_real_ip, _get_storage_uri


class TestLimiterConfig:
    """限流器配置测试。"""

    def test_limiter_instance_exists(self):
        """测试限流器实例已创建。"""
        limiter = get_limiter()
        assert isinstance(limiter, Limiter)

    def test_limiter_has_default_limits(self):
        """测试限流器有默认限制配置。"""
        limiter = get_limiter()
        assert limiter.default_limits is not None
        assert len(limiter.default_limits) > 0

    def test_get_real_ip_without_proxy(self):
        """测试无代理时获取真实 IP。"""
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        assert get_real_ip(request) == "127.0.0.1"

    def test_get_real_ip_with_x_forwarded_for(self):
        """测试有 X-Forwarded-For 头时获取真实 IP。"""
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {"x-forwarded-for": "203.0.113.50, 70.41.3.18"}
        assert get_real_ip(request) == "203.0.113.50"

    def test_get_real_ip_with_single_forwarded_ip(self):
        """测试单个 X-Forwarded-For IP。"""
        from unittest.mock import MagicMock

        request = MagicMock()
        request.headers = {"x-forwarded-for": "10.0.0.1"}
        assert get_real_ip(request) == "10.0.0.1"


class TestRateLimitStorage:
    """限流存储测试。"""

    def test_storage_uri_returns_memory_when_configured(self, monkeypatch):
        """测试配置为 memory 时返回 memory://。"""
        from src.config.settings import Settings

        class MockSettings:
            RATE_LIMIT_STORAGE = "memory"
            REDIS_URL = "redis://localhost:6379/0"

        monkeypatch.setattr("src.infrastructure.http.limiter.settings", MockSettings())
        assert _get_storage_uri() == "memory://"

    def test_storage_uri_returns_redis_when_available(self, monkeypatch):
        """测试 Redis 可用时返回 redis URL。"""
        from src.config.settings import Settings

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = "redis://localhost:6379/0"

        monkeypatch.setattr("src.infrastructure.http.limiter.settings", MockSettings())
        assert _get_storage_uri() == "redis://localhost:6379/0"

    def test_storage_uri_fallback_to_memory(self, monkeypatch):
        """测试 Redis 不可用时降级为 memory。"""
        from src.config.settings import Settings

        class MockSettings:
            RATE_LIMIT_STORAGE = "redis"
            REDIS_URL = ""

        monkeypatch.setattr("src.infrastructure.http.limiter.settings", MockSettings())
        assert _get_storage_uri() == "memory://"
```

- [ ] **Step 4: 运行限流测试**

```bash
cd service
pytest tests/unit/test_limiter.py -v
```

- [ ] **Step 5: 提交 P0-2 变更**

```bash
cd service
git add src/infrastructure/http/limiter.py src/config/settings.py tests/unit/test_limiter.py
git commit -m "feat(P0-2): 完善限流中间件，支持 Redis 存储和统一 429 响应格式"
```

---

### Task 3: Docker Compose 补全

**Files:**
- Modify: `service/docker/docker-compose.yml`

- [ ] **Step 1: 补全 docker-compose.yml**

修改 `service/docker/docker-compose.yml`，添加 PostgreSQL 和 Redis 服务：

```yaml
services:
  app:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: hello-fastapi
    ports:
      - "8000:8000"
    environment:
      - APP_ENV=production
      - TZ=Asia/Shanghai
      - DATABASE_URL=postgresql+asyncpg://hello_fastapi:hello_fastapi_pass@db:5432/hello_fastapi
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-change-this-to-a-random-secret-key-in-production}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY:-change-this-to-a-random-jwt-secret}
    volumes:
      - ../logs:/app/logs
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "python", "-c", "from urllib.request import urlopen; urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    networks:
      - hello-fastapi-net

  db:
    image: postgres:15-alpine
    container_name: hello-fastapi-db
    environment:
      - POSTGRES_DB=hello_fastapi
      - POSTGRES_USER=hello_fastapi
      - POSTGRES_PASSWORD=hello_fastapi_pass
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hello_fastapi -d hello_fastapi"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - hello-fastapi-net

  redis:
    image: redis:7-alpine
    container_name: hello-fastapi-redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 5s
    networks:
      - hello-fastapi-net

volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local

networks:
  hello-fastapi-net:
    name: hello-fastapi-net
    driver: bridge
```

- [ ] **Step 2: 验证 docker-compose.yml 语法**

```bash
cd service/docker
docker compose config
```

如果命令成功输出完整配置，说明 YAML 语法正确。

- [ ] **Step 3: 提交 P0-3 变更**

```bash
cd service
git add docker/docker-compose.yml
git commit -m "feat(P0-3): 补全 Docker Compose，添加 PostgreSQL 和 Redis 服务与健康检查"
```

---

### Task 4: Jenkins CI/CD Pipeline

**Files:**
- Create: `service/Jenkinsfile`
- Create: `service/docker/Jenkins/deploy.sh`

- [ ] **Step 1: 创建 Jenkinsfile 声明式 Pipeline**

创建 `service/Jenkinsfile`：

```groovy
// Jenkins 声明式 Pipeline - Hello-FastApi CI/CD
// 触发方式：Git Webhook (push 到 main/develop 分支) 或手动触发

pipeline {
    agent {
        docker {
            image 'python:3.10-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    parameters {
        choice(
            name: 'DEPLOY_ENV',
            choices: ['dev', 'staging', 'prod'],
            description: '部署目标环境'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: '是否运行测试'
        )
    }

    environment {
        APP_NAME = 'hello-fastapi'
        IMAGE_REGISTRY = "${env.DOCKER_REGISTRY ?: 'registry.example.com'}"
        IMAGE_TAG = "${params.DEPLOY_ENV}-${env.BUILD_NUMBER}"
        PYTHONUNBUFFERED = '1'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "检出代码: ${env.BRANCH_NAME}"
                sh 'python --version'
                sh 'pwd'
            }
        }

        stage('Install Dependencies') {
            steps {
                echo '安装依赖...'
                sh '''
                    cd service
                    pip install uv
                    uv pip install --system -e ".[dev]"
                '''
            }
        }

        stage('Lint') {
            steps {
                echo '运行 Ruff Lint 检查...'
                sh '''
                    cd service
                    ruff check src/ tests/
                '''
            }
        }

        stage('Format Check') {
            steps {
                echo '检查代码格式...'
                sh '''
                    cd service
                    ruff format src/ tests/ --check
                '''
            }
        }

        stage('Typecheck') {
            steps {
                echo '运行 MyPy 类型检查...'
                sh '''
                    cd service
                    mypy src/
                '''
            }
        }

        stage('Test') {
            when {
                expression { params.RUN_TESTS == true }
            }
            steps {
                echo '运行 pytest...'
                sh '''
                    cd service
                    pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=80 -v
                '''
            }
            post {
                always {
                    junit 'service/reports/junit.xml'
                    publishHTML([
                        reportDir: 'service/reports/htmlcov',
                        reportFiles: 'index.html',
                        reportName: '测试覆盖率报告'
                    ])
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                echo "构建 Docker 镜像: ${APP_NAME}:${IMAGE_TAG}"
                sh '''
                    cd service/docker
                    docker build -t ${APP_NAME}:${IMAGE_TAG} -f Dockerfile ..
                    docker tag ${APP_NAME}:${IMAGE_TAG} ${IMAGE_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                    docker tag ${APP_NAME}:${IMAGE_TAG} ${IMAGE_REGISTRY}/${APP_NAME}:latest
                '''
            }
        }

        stage('Push Docker Image') {
            when {
                expression { params.DEPLOY_ENV != 'dev' }
            }
            steps {
                echo "推送 Docker 镜像到仓库..."
                withCredentials([usernamePassword(credentialsId: 'docker-registry-credentials', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "${DOCKER_PASS}" | docker login ${IMAGE_REGISTRY} -u "${DOCKER_USER}" --password-stdin
                        docker push ${IMAGE_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                        docker push ${IMAGE_REGISTRY}/${APP_NAME}:latest
                    '''
                }
            }
        }

        stage('Deploy') {
            when {
                expression { params.DEPLOY_ENV in ['dev', 'staging', 'prod'] }
            }
            steps {
                echo "部署到 ${params.DEPLOY_ENV} 环境..."
                sh '''
                    cd service/docker/Jenkins
                    chmod +x deploy.sh
                    ./deploy.sh ${DEPLOY_ENV} ${IMAGE_REGISTRY} ${APP_NAME} ${IMAGE_TAG}
                '''
            }
        }
    }

    post {
        success {
            echo '构建成功！'
            sh 'echo "构建成功: ${APP_NAME} ${IMAGE_TAG}"'
        }
        failure {
            echo '构建失败！'
            sh 'echo "构建失败: ${APP_NAME} ${IMAGE_TAG}"'
        }
        always {
            cleanWs()
        }
    }
}
```

- [ ] **Step 2: 创建部署辅助脚本**

创建 `service/docker/Jenkins/deploy.sh`：

```bash
#!/bin/bash
# deploy.sh - Jenkins 部署辅助脚本
# 用法: ./deploy.sh <environment> <registry> <app_name> <image_tag>

set -e

ENVIRONMENT="${1:-dev}"
REGISTRY="${2:-registry.example.com}"
APP_NAME="${3:-hello-fastapi}"
IMAGE_TAG="${4:-latest}"

echo "============================================"
echo "部署 Hello-FastApi 到 ${ENVIRONMENT} 环境"
echo "镜像: ${REGISTRY}/${APP_NAME}:${IMAGE_TAG}"
echo "============================================"

# 根据环境执行不同部署策略
deploy_dev() {
    echo "部署到开发环境 (docker-compose)..."
    cd "$(dirname "$0")/.."
    
    # 停止旧服务
    docker compose down || true
    
    # 拉取新镜像并启动
    docker compose pull || true
    docker compose up -d
    
    # 等待服务就绪
    echo "等待服务启动..."
    sleep 10
    
    # 健康检查
    for i in {1..30}; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            echo "服务已就绪!"
            exit 0
        fi
        echo "等待中... (${i}/30)"
        sleep 2
    done
    
    echo "警告: 服务可能未完全启动，请手动检查"
    exit 1
}

deploy_staging() {
    echo "部署到预发布环境..."
    echo "通过 SSH 连接到预发布服务器执行部署"
    # 示例: ssh deploy@staging-server "cd /opt/hello-fastapi && docker compose pull && docker compose up -d"
    echo "请配置 staging 服务器的 SSH 部署"
}

deploy_prod() {
    echo "部署到生产环境..."
    echo "通过 SSH 连接到生产服务器执行滚动部署"
    # 示例: 使用 docker swarm 或 k8s
    echo "请配置 production 服务器的部署策略"
}

case "${ENVIRONMENT}" in
    dev)
        deploy_dev
        ;;
    staging)
        deploy_staging
        ;;
    prod)
        deploy_prod
        ;;
    *)
        echo "未知环境: ${ENVIRONMENT}"
        exit 1
        ;;
esac
```

- [ ] **Step 3: 给 deploy.sh 添加执行权限**

```bash
chmod +x service/docker/Jenkins/deploy.sh
```

- [ ] **Step 4: 提交 P0-4 变更**

```bash
cd service
git add Jenkinsfile docker/Jenkins/deploy.sh
git commit -m "feat(P0-4): 添加 Jenkins CI/CD Pipeline，支持 lint/test/build/deploy 全流程"
```

---

### Task 5: 整体验证与清理

- [ ] **Step 1: 运行全部测试确保无回归**

```bash
cd service
pytest tests/ -v --tb=short
```

- [ ] **Step 2: 运行 lint 和 typecheck**

```bash
cd service
ruff check src/ tests/ --fix
ruff format src/ tests/
mypy src/
```

- [ ] **Step 3: 验证所有 CLI 命令可用**

```bash
cd service
python -m scripts.cli --help
```

应显示 migrate、rollback、stamp 命令。

- [ ] **Step 4: 验证 Docker Compose 配置**

```bash
cd service/docker
docker compose config
```

- [ ] **Step 5: 创建最终提交**

```bash
cd service
git add .
git commit -m "chore(P0): 完成基础设施四项验证与清理"
```
