# SQLModel 原生仓储基类重构计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用 SQLModel 原生 API 替代 fastcrud，创建泛型仓储基类消除模板代码

**Architecture:** 在 `src/infrastructure/repositories/base.py` 创建 `GenericRepository[ModelT, EntityT]` 泛型基类，封装 SQLModel 原生的单表 CRUD 操作。8 个具体仓储继承基类，移除 FastCRUD 依赖。

**Tech Stack:** SQLModel, SQLAlchemy async, Python Generics (TypeVar)

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `src/infrastructure/repositories/base.py` | **新建** | 泛型仓储基类 |
| `src/infrastructure/repositories/user_repository.py` | **修改** | 继承基类，移除 FastCRUD |
| `src/infrastructure/repositories/role_repository.py` | **修改** | 继承基类 |
| `src/infrastructure/repositories/menu_repository.py` | **修改** | 继承基类 |
| `src/infrastructure/repositories/department_repository.py` | **修改** | 继承基类 |
| `src/infrastructure/repositories/dictionary_repository.py` | **修改** | 继承基类 |
| `src/infrastructure/repositories/system_config_repository.py` | **修改** | 继承基类 |
| `src/infrastructure/repositories/ip_rule_repository.py` | **修改** | 继承基类 |
| `src/infrastructure/repositories/log_repository.py` | **修改** | 继承基类 |
| `tests/unit/infrastructure/repositories/test_*.py` (8 个) | **修改** | 移除 FastCRUD Mock |
| `pyproject.toml` | **修改** | 移除 fastcrud 依赖 |
| `mypy.ini` | **修改** | 移除 fastcrud 忽略配置 |

---

### Task 1: 创建 GenericRepository 泛型基类

**Files:**
- Create: `src/infrastructure/repositories/base.py`
- Test: `tests/unit/infrastructure/repositories/test_base_repository.py`

- [ ] **Step 1: 创建泛型基类**

```python
"""通用仓储基类。

基于 SQLModel 原生 API，提供单表 CRUD 操作的泛型实现。
子类需指定 ModelT (SQLModel 表模型) 和 EntityT (领域实体)。
"""

from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, col, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelT = TypeVar("ModelT", bound=SQLModel)
EntityT = TypeVar("EntityT")


class GenericRepository(Generic[ModelT, EntityT]):
    """通用仓储基类，封装 SQLModel 原生的单表 CRUD。

    子类需实现：
    - _model_class: 返回 SQLModel 表模型类
    - _to_domain: 将表模型转为领域实体
    - _from_domain: 将领域实体转为表模型
    - _primary_key: 主键字段名（默认 "id"）
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def _model_class(self) -> type[ModelT]:
        """返回 SQLModel 表模型类。子类必须实现。"""
        raise NotImplementedError

    def _to_domain(self, model: ModelT) -> EntityT:
        """将表模型转为领域实体。子类必须实现。"""
        raise NotImplementedError

    def _from_domain(self, entity: EntityT) -> ModelT:
        """将领域实体转为表模型。子类必须实现。"""
        raise NotImplementedError

    @property
    def _primary_key(self) -> str:
        """主键字段名，默认 id。"""
        return "id"

    async def get_by_id(self, item_id: str) -> EntityT | None:
        """根据 ID 获取单个实体。"""
        stmt = select(self._model_class).where(
            getattr(col(self._model_class), self._primary_key) == item_id
        )
        result = await self.session.exec(stmt)
        model = result.first()
        return self._to_domain(model) if model else None

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        **filters: Any,
    ) -> list[EntityT]:
        """获取实体列表（分页 + 筛选）。"""
        stmt = select(self._model_class)
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(col(self._model_class), field) == value)

        offset = (page_num - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        result = await self.session.exec(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def create(self, entity: EntityT) -> EntityT:
        """创建新实体。"""
        model = self._from_domain(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def update(self, entity: EntityT) -> EntityT:
        """更新现有实体。"""
        model = self._from_domain(entity)
        merged = await self.session.merge(model)
        await self.session.flush()
        await self.session.refresh(merged)
        return self._to_domain(merged)

    async def delete(self, item_id: str) -> bool:
        """根据 ID 删除实体。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(self._model_class).where(
            getattr(col(self._model_class), self._primary_key) == item_id
        )
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return (result.rowcount or 0) > 0

    async def count(self, **filters: Any) -> int:
        """统计实体数量（支持筛选）。"""
        from sqlalchemy import func as sa_func

        stmt = select(sa_func.count()).select_from(self._model_class)
        for field, value in filters.items():
            if value is not None:
                stmt = stmt.where(getattr(col(self._model_class), field) == value)
        result = await self.session.exec(stmt)
        return result.one()
```

- [ ] **Step 2: 创建基类单元测试**

```python
"""GenericRepository 基类单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import SQLModel, Field

from src.infrastructure.repositories.base import GenericRepository


class TestModel(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str


class TestEntity:
    def __init__(self, id: str, name: str) -> None:
        self.id = id
        self.name = name

    def __eq__(self, other):
        return isinstance(other, TestEntity) and self.id == other.id and self.name == other.name


class ConcreteRepo(GenericRepository[TestModel, TestEntity]):
    @property
    def _model_class(self) -> type[TestModel]:
        return TestModel

    def _to_domain(self, model: TestModel) -> TestEntity:
        return TestEntity(id=model.id, name=model.name)

    def _from_domain(self, entity: TestEntity) -> TestModel:
        return TestModel(id=entity.id, name=entity.name)


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def repo(mock_session):
    return ConcreteRepo(mock_session)


@pytest.mark.unit
class TestGenericRepository:
    def test_init(self, repo, mock_session):
        assert repo.session is mock_session

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repo, mock_session):
        mock_model = MagicMock(spec=TestModel)
        mock_model.id = "1"
        mock_model.name = "test"
        mock_result = MagicMock()
        mock_result.first.return_value = mock_model
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("1")
        assert result is not None
        assert result.id == "1"
        assert result.name == "test"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id("not-exist")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        mock_model = MagicMock(spec=TestModel)
        mock_model.id = "1"
        mock_model.name = "test"
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_model]
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.get_all(page_num=1, page_size=10)
        assert len(result) == 1
        assert result[0].id == "1"

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.one.return_value = 42
        mock_session.exec = AsyncMock(return_value=mock_result)

        result = await repo.count()
        assert result == 42
```

- [ ] **Step 3: 运行测试验证**

```bash
pytest tests/unit/infrastructure/repositories/test_base_repository.py -v
```

预期：5 个测试全部通过

- [ ] **Step 4: 运行 mypy 验证类型安全**

```bash
mypy src/infrastructure/repositories/base.py
```

---

### Task 2: 迁移 UserRepository

**Files:**
- Modify: `src/infrastructure/repositories/user_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_user_repository.py`

- [ ] **Step 1: 重写 UserRepository 继承基类**

```python
"""使用 SQLModel 原生 API 实现的用户仓库。"""

from typing import Any

from sqlalchemy import delete as sa_delete
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.user import UserEntity
from src.domain.repositories.user_repository import UserRepositoryInterface
from src.infrastructure.database.models import User
from src.infrastructure.repositories.base import GenericRepository


class UserRepository(GenericRepository[User, UserEntity], UserRepositoryInterface):
    """UserRepositoryInterface 的 SQLModel 原生实现。"""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    @property
    def _model_class(self) -> type[User]:
        return User

    def _to_domain(self, model: User) -> UserEntity:
        return model.to_domain()

    def _from_domain(self, entity: UserEntity) -> User:
        return User.from_domain(entity)

    async def get_by_username(self, username: str) -> UserEntity | None:
        """根据用户名获取用户。"""
        from sqlmodel import select

        stmt = select(User).where(User.username == username)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def get_by_email(self, email: str) -> UserEntity | None:
        """根据邮箱获取用户。"""
        from sqlmodel import select

        stmt = select(User).where(User.email == email)
        result = await self.session.exec(stmt)
        model = result.first()
        return model.to_domain() if model else None

    async def get_all(
        self,
        page_num: int = 1,
        page_size: int = 10,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> list[UserEntity]:
        """获取用户列表（支持筛选和分页）。"""
        filters: dict[str, Any] = {}
        if username:
            filters["username"] = username
        if phone:
            filters["phone"] = phone
        if email:
            filters["email"] = email
        if is_active is not None:
            filters["is_active"] = is_active
        if dept_id is not None:
            filters["dept_id"] = dept_id

        return await super().get_all(page_num, page_size, **filters)

    async def count(
        self,
        username: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        is_active: int | None = None,
        dept_id: str | None = None,
    ) -> int:
        """获取用户总数（支持筛选）。"""
        filters: dict[str, Any] = {}
        if username:
            filters["username"] = username
        if phone:
            filters["phone"] = phone
        if email:
            filters["email"] = email
        if is_active is not None:
            filters["is_active"] = is_active
        if dept_id is not None:
            filters["dept_id"] = dept_id

        return await super().count(**filters)

    async def batch_delete(self, user_ids: list[str]) -> int:
        """批量删除用户。"""
        if not user_ids:
            return 0
        stmt = sa_delete(User).where(User.id.in_(user_ids))
        result = await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        return result.rowcount or 0

    async def update_status(self, user_id: str, is_active: int) -> bool:
        """更新用户启用状态。"""
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        user.is_active = is_active
        await self.session.flush()
        return True

    async def reset_password(self, user_id: str, hashed_password: str) -> bool:
        """重置用户密码。"""
        user = await self.get_by_id(user_id)
        if user is None:
            return False
        user.password = hashed_password
        await self.session.flush()
        return True
```

- [ ] **Step 2: 更新 UserRepository 测试**

移除所有 `repo._crud.*` 的 Mock，改为 Mock `repo.session.exec`：

```python
# 原代码（删除）:
repo._crud.get = AsyncMock(return_value=mock_model)
repo._crud.get_multi = AsyncMock(return_value={"data": [mock_model]})
repo._crud.count = AsyncMock(return_value=100)
repo._crud.create = AsyncMock(return_value=None)

# 新代码（使用 session.exec mock）:
mock_result = MagicMock()
mock_result.first.return_value = mock_model  # 对应 get_by_id
mock_result.scalars.return_value.all.return_value = [mock_model]  # 对应 get_all
mock_result.one.return_value = 100  # 对应 count
repo.session.exec = AsyncMock(return_value=mock_result)
```

- [ ] **Step 3: 验证测试通过**

```bash
pytest tests/unit/infrastructure/repositories/test_user_repository.py -v
```

---

### Task 3: 迁移 DepartmentRepository

**Files:**
- Modify: `src/infrastructure/repositories/department_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_department_repository.py`

关键点：继承基类后，`get_by_id` 和 `count` 可直接使用基类实现。保留 `get_by_name`, `get_by_code`, `get_by_parent_id`, `get_filtered` 等特有方法。

---

### Task 4: 迁移 DictionaryRepository

**Files:**
- Modify: `src/infrastructure/repositories/dictionary_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_dictionary_repository.py`

关键点：继承基类后，`get_by_id`, `count` 使用基类。保留 `get_by_name`, `get_by_parent_id`, `get_filtered`, `get_max_sort` 等特有方法。

---

### Task 5: 迁移 SystemConfigRepository

**Files:**
- Modify: `src/infrastructure/repositories/system_config_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_system_config_repository.py`

关键点：继承基类后，`get_by_id` 使用基类，保留 `get_by_key` 特有方法。`count` 使用基类实现。

---

### Task 6: 迁移 MenuRepository

**Files:**
- Modify: `src/infrastructure/repositories/menu_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_menu_repository.py`

关键点：继承基类后，`get_by_id` 使用基类。保留 `get_all`（带 selectinload）、`get_by_name`, `get_by_parent_id`、delete cascade 逻辑。`_meta_crud` 改为内嵌 `_meta_repo` 或独立方法。

---

### Task 7: 迁移 RoleRepository

**Files:**
- Modify: `src/infrastructure/repositories/role_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_role_repository.py`

关键点：继承基类后，`get_by_id` 和 `count` 使用基类。保留 `get_by_name`, `get_by_code`, 用户角色关联方法，菜单关联方法。

---

### Task 8: 迁移 IPRuleRepository

**Files:**
- Modify: `src/infrastructure/repositories/ip_rule_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_ip_rule_repository.py`

关键点：继承基类后，`get_by_id` 使用基类。保留 `get_ip_rules`（分页+筛选+排序），`delete_ip_rules`，`clear_ip_rules`，`get_effective_ip_rules`。

---

### Task 9: 迁移 LogRepository

**Files:**
- Modify: `src/infrastructure/repositories/log_repository.py`
- Modify: `tests/unit/infrastructure/repositories/test_log_repository.py`

关键点：继承基类后，内部使用基类方法封装登录日志和操作日志的 CRUD。保留分页查询方法。

---

### Task 10: 移除 fastcrud 依赖，运行全量验证

**Files:**
- Modify: `pyproject.toml`
- Modify: `mypy.ini`

- [ ] **Step 1: 移除 pyproject.toml 中的 fastcrud 依赖**

```toml
# 删除此行:
"fastcrud>=0.15.0",
```

- [ ] **Step 2: 移除 mypy.ini 中的 fastcrud 忽略配置**

```ini
# 删除此段:
[mypy-fastcrud.*]
ignore_errors = True
```

- [ ] **Step 3: 移除 pyproject.toml 中的 fastcrud 警告过滤**

```toml
# 删除此行:
"ignore::DeprecationWarning:fastcrud",
```

- [ ] **Step 4: 全量测试验证**

```bash
# 安装依赖（移除 fastcrud）
uv sync

# 运行 lint, type check, tests
ruff check src/ && ruff format src/
mypy src/
pytest tests/ --ignore=tests/ui_test.py --tb=no -q
```

预期结果：
- ruff: 0 errors
- mypy: Success (0 errors)
- pytest: 1851 passed, 0 failed

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "refactor: replace fastcrud with SQLModel native GenericRepository base class"
```

---

## 验收标准

1. ✅ `fastcrud` 依赖完全移除
2. ✅ 所有 1851 个测试通过
3. ✅ mypy 类型检查通过
4. ✅ ruff lint 通过
5. ✅ 代码量减少（预计减少 300+ 行模板代码）
6. ✅ 无功能回归（API 行为完全一致）
