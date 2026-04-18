---
name: crud-generator
description: >
  根据数据库表结构，自动生成符合当前项目 DDD 分层架构的完整前后端 CRUD 代码。
  此技能应在用户需要新建业务模块、根据表结构生成代码、或开发新的 CRUD 功能时使用。
  生成的代码包括后端 ORM 模型、领域实体、仓储接口/实现、DTO、应用服务、API 路由、
  依赖注入、单元测试，以及前端 API 类、类型定义、Hook、表单、页面组件。
  同时提供验证流程确保代码正确性。
---

# CRUD 代码生成器

## 概述

给定一个数据库表结构定义，按照当前项目的 DDD 架构和前端组件模式，生成完整的前后端 CRUD 代码，并通过单元测试和联调验证正确性。

## 触发条件

当用户提出以下需求时使用此技能：
- "根据表结构生成代码"
- "新建一个业务模块"
- "开发一个 CRUD 功能"
- "帮我写一个 xxx 管理模块"
- 提供了数据库表结构（SQL/DDL/字段列表）并要求开发

## 输入规范

接收数据库表结构定义，格式示例：

```
模块名称: product（英文，单数）
模块中文名: 商品
表名: sys_products
列表模式: paginated（paginated | tree）
字段列表:
  - name: str, 必填, 最大128字符, 商品名称
  - code: str, 唯一, 最大64字符, 商品编码
  - price: float, 默认0, 价格
  - category_id: str, 可选, 外键关联 sys_categories.id, 分类ID
  - is_active: int, 默认1, 是否启用
  - sort_order: int, 默认0, 排序号
  - description: str, 可选, 最大256字符, 描述
```

关键识别规则：
- 如果字段包含 `parent_id` 且外键指向自身，则 `列表模式=tree`
- 否则默认 `列表模式=paginated`
- `is_active` 字段自动识别为状态开关
- `sort_order` / `rank` 字段自动识别为排序
- `description` 字段自动映射为文本域
- `created_time` / `updated_time` 时间戳字段自动生成，无需在输入中指定

## 代码生成流水线

按以下顺序生成代码，每一步依赖前一步的输出：

```
1. ORM 模型 → 2. 领域实体 → 3. 仓储接口 → 4. 仓储实现
→ 5. DTO → 6. 应用服务 → 7. API 路由 → 8. 依赖注入
→ 9. 模块注册(修改 __init__.py) → 10. 单元测试
→ 11. 前端 API → 12. 前端视图(hook/form/index/types/rule)
→ 13. 前端模块注册 → 14. 验证
```

## 命名规范速查

| 概念 | 英文(单数) | 英文大写 | 中文 |
|------|-----------|---------|------|
| 模块名 | product | Product | 商品 |
| ORM 类 | Product | | |
| 表名 | sys_products | | |
| 领域实体 | ProductEntity | | |
| 仓储接口 | ProductRepositoryInterface | | |
| 仓储实现 | ProductRepository | | |
| 服务类 | ProductService | | |
| DTO创建 | ProductCreateDTO | | |
| DTO更新 | ProductUpdateDTO | | |
| DTO响应 | ProductResponseDTO | | |
| DTO查询 | ProductListQueryDTO | | |
| API路由类 | ProductRouter | | |
| 依赖工厂 | get_product_service | | |
| API路径前缀 | /product | | |
| 权限码 | product:view/add/edit/delete | | |
| 前端API | productApi | | |
| 前端组件名 | SystemProduct | | |

## 变量占位符说明

模板中使用以下占位符，生成时需替换：

- `{{Name}}` - 大驼峰模块名，如 Product
- `{{name}}` - 小写模块名，如 product
- `{{NameLower}}` - 全小写模块名（无分隔），如 product
- `{{table_name}}` - 数据库表名，如 sys_products
- `{{chinese_name}}` - 中文名称，如 商品
- `{{list_mode}}` - 列表模式：paginated 或 tree
- `{{fields}}` - 自定义字段定义区域（不含 id/时间戳/标准字段）
- `{{field_imports}}` - 字段特殊导入（如 Text, SmallInteger 等）

---

## 后端模板

### 1. ORM 模型 (`service/src/infrastructure/database/models/{{name}}.py`)

```python
"""{{chinese_name}}实体模型。"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func{{field_imports}}
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.{{name}} import {{Name}}Entity


class {{Name}}(SQLModel, table=True):
    """{{chinese_name}}实体{{tree_suffix}}。"""

    __tablename__ = "{{table_name}}"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
{{fields_orm}}
    is_active: int = Field(default=1)  # 是否启用
    creator_id: str | None = Field(default=None, max_length=150)  # 创建人ID
    modifier_id: str | None = Field(default=None, max_length=150)  # 修改人ID
{{parent_id_field}}
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now()))
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "{{Name}}Entity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.{{name}} import {{Name}}Entity

        return {{Name}}Entity(
            id=self.id,
{{fields_to_domain}}
            is_active=self.is_active,
            creator_id=self.creator_id,
            modifier_id=self.modifier_id,
{{parent_id_to_domain}}
            created_time=self.created_time,
            updated_time=self.updated_time,
            description=self.description,
        )

    @classmethod
    def from_domain(cls, entity: "{{Name}}Entity") -> "{{Name}}":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
{{fields_from_domain}}
            is_active=entity.is_active,
            creator_id=entity.creator_id,
            modifier_id=entity.modifier_id,
{{parent_id_from_domain}}
            created_time=entity.created_time,
            updated_time=entity.updated_time,
            description=entity.description,
        )

    def __repr__(self) -> str:
        return f"<{{Name}}(id={self.id}, name={self.name})>"
```

**字段生成规则**：
- `str` 类型必填: `field_name: str = Field(max_length=XXX)`
- `str` 类型可选: `field_name: str | None = Field(default=None, max_length=XXX)`
- `str` 类型唯一: `field_name: str = Field(max_length=XXX, unique=True)`
- `str` 类型长文本: `field_name: str = Field(sa_column=Column(Text, nullable=False))`，需额外导入 `Text`
- `int` 类型: `field_name: int = Field(default=XXX)`
- `float` 类型: `field_name: float = Field(default=XXX)`
- `parent_id` 字段(树形): `parent_id: str | None = Field(default=None, foreign_key="{{table_name}}.id")`
- 排序字段: `sort_order: int = Field(default=0)  # 排序号`

### 2. 领域实体 (`service/src/domain/entities/{{name}}.py`)

```python
"""{{chinese_name}}领域实体。

定义{{chinese_name}}的领域实体类，使用 dataclass 实现。
不依赖任何 ORM 或外部库。
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class {{Name}}Entity:
    """{{chinese_name}}领域实体{{tree_suffix}}。

    Attributes:
        id: 唯一标识（32位UUID字符串）
{{fields_entity_doc}}
        is_active: 是否启用
        creator_id: 创建人ID
        modifier_id: 修改人ID
{{parent_id_doc}}
        created_time: 创建时间
        updated_time: 更新时间
        description: 描述
    """

    id: str
{{fields_entity}}
    is_active: int = 1
    creator_id: str | None = None
    modifier_id: str | None = None
{{parent_id_entity}}
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None
```

### 3. 仓储接口 (`service/src/domain/repositories/{{name}}_repository.py`)

**分页模式**：

```python
"""{{chinese_name}}仓储接口。

定义{{chinese_name}}仓储的抽象接口，遵循依赖倒置原则。
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from sqlmodel.ext.asyncio.session import AsyncSession

if TYPE_CHECKING:
    from src.infrastructure.database.models import {{Name}}


class {{Name}}RepositoryInterface(ABC):
    """{{chinese_name}}的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, {{filter_params}}) -> list["{{Name}}"]:
        """获取{{chinese_name}}列表（支持分页和筛选）。"""
        ...

    @abstractmethod
    async def count(self, session: AsyncSession, {{filter_params}}) -> int:
        """统计{{chinese_name}}数量（支持筛选）。"""
        ...

    @abstractmethod
    async def get_by_id(self, {{name}}_id: str, session: AsyncSession) -> "{{Name}} | None":
        """根据 ID 获取{{chinese_name}}。"""
        ...

    @abstractmethod
    async def get_by_{{unique_field}}(self, {{unique_field}}: str, session: AsyncSession) -> "{{Name}} | None":
        """根据{{unique_field_cn}}获取{{chinese_name}}。"""
        ...

    @abstractmethod
    async def create(self, {{name}}: "{{Name}}", session: AsyncSession) -> "{{Name}}":
        """创建{{chinese_name}}。"""
        ...

    @abstractmethod
    async def update(self, {{name}}: "{{Name}}", session: AsyncSession) -> "{{Name}}":
        """更新{{chinese_name}}。"""
        ...

    @abstractmethod
    async def delete(self, {{name}}_id: str, session: AsyncSession) -> bool:
        """删除{{chinese_name}}。"""
        ...
```

**树形模式** - 额外追加 `get_by_parent_id` 方法，`get_all` 不分页：

```python
    @abstractmethod
    async def get_all(self, session: AsyncSession) -> list["{{Name}}"]:
        """获取所有{{chinese_name}}。"""
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list["{{Name}}"]:
        """根据父级 ID 获取子级{{chinese_name}}。"""
        ...
```

### 4. 仓储实现 (`service/src/infrastructure/repositories/{{name}}_repository.py`)

**分页模式**：

```python
"""使用 SQLModel 和 FastCRUD 实现的{{chinese_name}}仓库。"""

from fastcrud import FastCRUD
from sqlalchemy import func as sa_func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.repositories.{{name}}_repository import {{Name}}RepositoryInterface
from src.infrastructure.database.models import {{Name}}


class {{Name}}Repository({{Name}}RepositoryInterface):
    """{{chinese_name}}仓储的 SQLModel 实现。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD({{Name}})

    async def get_all(self, session: AsyncSession, page_num: int = 1, page_size: int = 10, {{filter_params}}) -> list[{{Name}}]:
        """获取{{chinese_name}}列表（支持分页和筛选）。"""
        offset = (page_num - 1) * page_size
        query = select({{Name}})
{{filter_where_clauses}}
        query = query.offset(offset).limit(page_size)
        result = await session.exec(query)
        return list(result.all())

    async def count(self, session: AsyncSession, {{filter_params}}) -> int:
        """统计{{chinese_name}}数量（支持筛选）。"""
        count_query = select(sa_func.count()).select_from({{Name}})
{{filter_where_clauses_count}}
        result = await session.execute(count_query)
        return result.scalar_one()

    async def get_by_id(self, {{name}}_id: str, session: AsyncSession) -> {{Name}} | None:
        """根据 ID 获取{{chinese_name}}。"""
        return await self._crud.get(session, id={{name}}_id, schema_to_select={{Name}}, return_as_model=True)

    async def get_by_{{unique_field}}(self, {{unique_field}}: str, session: AsyncSession) -> {{Name}} | None:
        """根据{{unique_field_cn}}获取{{chinese_name}}。"""
        return await self._crud.get(session, {{unique_field}}={{unique_field}}, schema_to_select={{Name}}, return_as_model=True)

    async def create(self, {{name}}: {{Name}}, session: AsyncSession) -> {{Name}}:
        """创建{{chinese_name}}。"""
        return await self._crud.create(session, {{name}})

    async def update(self, {{name}}: {{Name}}, session: AsyncSession) -> {{Name}}:
        """更新{{chinese_name}}。"""
        from sqlalchemy import update as sa_update

        stmt = sa_update({{Name}}).where({{Name}}.id == {{name}}.id).values({{update_values}})
        await session.exec(stmt)  # type: ignore[arg-type]
        await session.flush()
        updated = await self.get_by_id({{name}}.id, session)
        return updated  # type: ignore[return-value]

    async def delete(self, {{name}}_id: str, session: AsyncSession) -> bool:
        """删除{{chinese_name}}。"""
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete({{Name}}).where({{Name}}.id == {{name}}_id)
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]
```

**树形模式** - `get_all` 不分页，额外实现 `get_by_parent_id`：

```python
    async def get_all(self, session: AsyncSession) -> list[{{Name}}]:
        """获取所有{{chinese_name}}，按排序号排序。"""
        result = await self._crud.get_multi(session, schema_to_select={{Name}}, return_as_model=True, return_total_count=False)
        items = result.get("data", [])
        return sorted(items, key=lambda d: d.sort_order)

    async def get_by_parent_id(self, parent_id: str | None, session: AsyncSession) -> list[{{Name}}]:
        """根据父级 ID 获取子级{{chinese_name}}，按排序号排序。"""
        result = await self._crud.get_multi(session, parent_id=parent_id, schema_to_select={{Name}}, return_as_model=True, return_total_count=False)
        items = result.get("data", [])
        return sorted(items, key=lambda d: d.sort_order)
```

### 5. DTO (`service/src/application/dto/{{name}}_dto.py`)

```python
"""应用层 - {{chinese_name}}领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_or_zero_to_none, empty_str_to_none{{validator_imports}}


class {{Name}}CreateDTO(BaseModel):
    """创建{{chinese_name}}请求"""

{{fields_create_dto}}
    isActive: int = Field(default=1, description="是否启用")
{{parent_id_create_dto}}
    description: str | None = Field(default=None, max_length=256)

{{create_validators}}


class {{Name}}UpdateDTO(BaseModel):
    """更新{{chinese_name}}请求"""

{{fields_update_dto}}
    isActive: int | None = Field(default=None, description="是否启用")
{{parent_id_update_dto}}
    description: str | None = Field(default=None, max_length=256)

{{update_validators}}


class {{Name}}ResponseDTO(BaseModel):
    """{{chinese_name}}响应"""

    id: str
{{fields_response_dto}}
    isActive: int = 1
    creatorId: str | None = None
    modifierId: str | None = None
{{parent_id_response_dto}}
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


{{query_dto_class}}
```

**DTO 字段映射规则**：
- ORM `snake_case` → DTO `camelCase`（如 `is_active` → `isActive`）
- `parentId` 使用 `normalize_optional_id` 验证器
- `description` 使用 `empty_str_to_none` 验证器
- `int` 可选字段使用 `empty_str_or_zero_to_none` 验证器

**分页模式 QueryDTO**：

```python
class {{Name}}ListQueryDTO(BaseModel):
    """{{chinese_name}}列表查询"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
{{fields_query_dto}}
```

**树形模式 QueryDTO**：

```python
class {{Name}}ListQueryDTO(BaseModel):
    """{{chinese_name}}列表查询请求"""

{{fields_query_dto}}
```

### 6. 应用服务 (`service/src/application/services/{{name}}_service.py`)

**分页模式**：

```python
"""应用层 - {{chinese_name}}服务。

提供{{chinese_name}}相关的业务逻辑，包括{{chinese_name}}的增删改查等操作。
"""

from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.dto.{{name}}_dto import {{Name}}CreateDTO, {{Name}}ListQueryDTO, {{Name}}ResponseDTO, {{Name}}UpdateDTO
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.{{name}}_repository import {{Name}}RepositoryInterface
from src.infrastructure.database.models import {{Name}}


class {{Name}}Service:
    """{{chinese_name}}操作的应用服务。"""

    def __init__(self, session: AsyncSession, {{name}}_repo: {{Name}}RepositoryInterface):
        """初始化{{chinese_name}}服务。

        Args:
            session: 数据库会话，用于事务控制
            {{name}}_repo: {{chinese_name}}仓储接口实例
        """
        self.session = session
        self.{{name}}_repo = {{name}}_repo

    async def get_{{name}}s(self, query: {{Name}}ListQueryDTO) -> tuple[list[{{Name}}ResponseDTO], int]:
        """获取{{chinese_name}}列表（分页）。

        Args:
            query: 查询参数

        Returns:
            {{chinese_name}}列表和总数
        """
        total = await self.{{name}}_repo.count(session=self.session, {{filter_args}})
        items = await self.{{name}}_repo.get_all(session=self.session, page_num=query.pageNum, page_size=query.pageSize, {{filter_args}})
        return [self._to_response(item) for item in items], total

    async def get_{{name}}(self, {{name}}_id: str) -> {{Name}}ResponseDTO:
        """根据ID获取{{chinese_name}}。"""
        item = await self.{{name}}_repo.get_by_id({{name}}_id, session=self.session)
        if item is None:
            raise NotFoundError(f"{{chinese_name}} ID '{{'{name}'}}_id' 不存在")
        return self._to_response(item)

    async def create_{{name}}(self, dto: {{Name}}CreateDTO) -> {{Name}}ResponseDTO:
        """创建{{chinese_name}}。

        Raises:
            ConflictError: {{unique_field_cn}}已存在
        """
        # 检查唯一字段
        existing = await self.{{name}}_repo.get_by_{{unique_field}}(dto.{{unique_field}}, session=self.session)
        if existing:
            raise ConflictError("{{unique_field_cn}}已存在")

        item = {{Name}}({{create_field_mapping}})
        item = await self.{{name}}_repo.create(item, session=self.session)
        await self.session.flush()
        return self._to_response(item)

    async def update_{{name}}(self, {{name}}_id: str, dto: {{Name}}UpdateDTO) -> {{Name}}ResponseDTO:
        """更新{{chinese_name}}。

        Raises:
            NotFoundError: {{chinese_name}}不存在
            ConflictError: {{unique_field_cn}}已被占用
        """
        item = await self.{{name}}_repo.get_by_id({{name}}_id, session=self.session)
        if item is None:
            raise NotFoundError(f"{{chinese_name}} ID '{{'{name}'}}_id' 不存在")

        # 检查唯一字段冲突
        if dto.{{unique_field}} is not None:
            existing = await self.{{name}}_repo.get_by_{{unique_field}}(dto.{{unique_field}}, session=self.session)
            if existing and existing.id != {{name}}_id:
                raise ConflictError("{{unique_field_cn}}已存在")
            item.{{unique_field}} = dto.{{unique_field}}

{{update_field_assignments}}

        item = await self.{{name}}_repo.update(item, session=self.session)
        await self.session.flush()
        return self._to_response(item)

    async def delete_{{name}}(self, {{name}}_id: str) -> bool:
        """删除{{chinese_name}}。

        Raises:
            NotFoundError: {{chinese_name}}不存在
        """
        if not await self.{{name}}_repo.delete({{name}}_id, session=self.session):
            raise NotFoundError(f"{{chinese_name}} ID '{{'{name}'}}_id' 不存在")
        return True

    @staticmethod
    def _to_response(item: {{Name}}) -> {{Name}}ResponseDTO:
        """将 {{Name}} 模型转换为响应 DTO。"""
        return {{Name}}ResponseDTO(
            id=item.id,
{{fields_to_response}}
            isActive=item.is_active,
            creatorId=item.creator_id,
            modifierId=item.modifier_id,
{{parent_id_to_response}}
            createdTime=item.created_time,
            updatedTime=item.updated_time,
            description=item.description,
        )
```

**树形模式** - 差异点：
- `get_{{name}}s` 返回 `list[{{Name}}ResponseDTO]`（无总数），无分页参数
- `create_{{name}}` 中检查 `parentId` 对应的父级存在性
- `update_{{name}}` 中防止将节点设为自己的子节点
- `delete_{{name}}` 中检查是否有子节点

### 7. API 路由 (`service/src/api/v1/{{name}}_router.py`)

**分页模式**：

```python
"""{{chinese_name}}管理路由模块。

提供{{chinese_name}}的增删改查功能。
路由前缀: /api/system/{{name}}
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import list_response, success_response
from src.api.dependencies import get_{{name}}_service, require_permission
from src.application.dto.{{name}}_dto import {{Name}}CreateDTO, {{Name}}ListQueryDTO, {{Name}}UpdateDTO
from src.application.services.{{name}}_service import {{Name}}Service


class {{Name}}Router(Routable):
    """{{chinese_name}}管理路由类，提供{{chinese_name}}增删改查功能。"""

    @post("")
    async def get_{{name}}_list(self, query: {{Name}}ListQueryDTO, service: {{Name}}Service = Depends(get_{{name}}_service), _: dict = Depends(require_permission("{{name}}:view"))) -> dict:
        """获取{{chinese_name}}列表（分页）。"""
        items, total = await service.get_{{name}}s(query)
        return list_response(list_data=[item.model_dump() for item in items], total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/create")
    async def create_{{name}}(self, dto: {{Name}}CreateDTO, service: {{Name}}Service = Depends(get_{{name}}_service), _: dict = Depends(require_permission("{{name}}:add"))) -> dict:
        """创建{{chinese_name}}。"""
        item = await service.create_{{name}}(dto)
        return success_response(data=item, message="创建成功", code=201)

    @get("/{{{name}}_id}")
    async def get_{{name}}(self, {{name}}_id: str, service: {{Name}}Service = Depends(get_{{name}}_service), _: dict = Depends(require_permission("{{name}}:view"))) -> dict:
        """获取{{chinese_name}}详情。"""
        item = await service.get_{{name}}({{name}}_id)
        return success_response(data=item)

    @put("/{{{name}}_id}")
    async def update_{{name}}(self, {{name}}_id: str, dto: {{Name}}UpdateDTO, service: {{Name}}Service = Depends(get_{{name}}_service), _: dict = Depends(require_permission("{{name}}:edit"))) -> dict:
        """更新{{chinese_name}}。"""
        item = await service.update_{{name}}({{name}}_id, dto)
        return success_response(data=item, message="更新成功")

    @delete("/{{{name}}_id}")
    async def delete_{{name}}(self, {{name}}_id: str, service: {{Name}}Service = Depends(get_{{name}}_service), _: dict = Depends(require_permission("{{name}}:delete"))) -> dict:
        """删除{{chinese_name}}。"""
        await service.delete_{{name}}({{name}}_id)
        return success_response(message="删除成功")
```

**树形模式** - 列表接口差异：
- `@post("/{{name}}")` 路由，接收 `dict = Body(default={})`
- 手动构建 `QueryDTO`，调用 `success_response(data=...)` 而非 `list_response`

### 8. 依赖注入 (`service/src/api/dependencies/{{name}}_service.py`)

```python
"""{{chinese_name}}应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.{{name}}_service import {{Name}}Service
from src.infrastructure.database import get_db
from src.infrastructure.repositories.{{name}}_repository import {{Name}}Repository


async def get_{{name}}_service(db: AsyncSession = Depends(get_db)) -> {{Name}}Service:
    """获取{{chinese_name}}服务实例。

    注入{{chinese_name}}仓储依赖。
    """
    {{name}}_repo = {{Name}}Repository(db)
    return {{Name}}Service(session=db, {{name}}_repo={{name}}_repo)
```

### 9. 模块注册（修改 `__init__.py`）

需要修改以下文件，追加对应的导入和 `__all__` 导出：

| 文件 | 追加内容 |
|------|---------|
| `infrastructure/database/models/__init__.py` | `from src.infrastructure.database.models.{{name}} import {{Name}}` + `__all__` 追加 `"{{Name}}"` |
| `domain/entities/__init__.py` | `from src.domain.entities.{{name}} import {{Name}}Entity` + `__all__` 追加 `"{{Name}}Entity"` |
| `domain/repositories/__init__.py` | `from src.domain.repositories.{{name}}_repository import {{Name}}RepositoryInterface` + `__all__` 追加 `"{{Name}}RepositoryInterface"` |
| `infrastructure/repositories/__init__.py` | `from src.infrastructure.repositories.{{name}}_repository import {{Name}}Repository` + `__all__` 追加 `"{{Name}}Repository"` |
| `application/dto/__init__.py` | 导入4个DTO类 + `__all__` 追加 |
| `application/services/__init__.py` | `from src.application.services.{{name}}_service import {{Name}}Service` + `__all__` 追加 `"{{Name}}Service"` |
| `api/dependencies/__init__.py` | `from src.api.dependencies.{{name}}_service import get_{{name}}_service` + `__all__` 追加 `"get_{{name}}_service"` |
| `api/v1/__init__.py` | 导入 `{{Name}}Router` + `system_router.include_router({{Name}}Router().router, prefix="/{{name}}", tags=["{{chinese_name}}管理"])` |
| `domain/__init__.py` | 追加 `{{Name}}Entity` 和 `{{Name}}RepositoryInterface` 导出 |

### 10. 单元测试 (`service/tests/unit/test_{{name}}_service.py`)

```python
"""{{chinese_name}}服务的单元测试。"""

from unittest.mock import AsyncMock

import pytest

from src.application.dto.{{name}}_dto import {{Name}}CreateDTO, {{Name}}ListQueryDTO, {{Name}}UpdateDTO
from src.application.services.{{name}}_service import {{Name}}Service
from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.database.models import {{Name}}


@pytest.mark.unit
class Test{{Name}}Service:
    """{{Name}}Service 测试类。"""

    @pytest.fixture
    def mock_session(self):
        """创建模拟数据库会话。"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_{{name}}_repo(self):
        """创建模拟{{chinese_name}}仓储。"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock(return_value=None)
        repo.get_by_{{unique_field}} = AsyncMock(return_value=None)
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=False)
        repo.count = AsyncMock(return_value=0)
        repo.get_all = AsyncMock(return_value=[])
        return repo

    @pytest.fixture
    def {{name}}_service(self, mock_session, mock_{{name}}_repo):
        """创建{{chinese_name}}服务实例。"""
        return {{Name}}Service(session=mock_session, {{name}}_repo=mock_{{name}}_repo)

    @pytest.mark.asyncio
    async def test_create_{{name}}_success(self, {{name}}_service, mock_{{name}}_repo, mock_session):
        """测试创建{{chinese_name}}成功。"""
        created = {{Name}}(id="test-id-1", {{unique_field}}="test_{{unique_field}}", is_active=1)
        mock_{{name}}_repo.get_by_{{unique_field}} = AsyncMock(return_value=None)
        mock_{{name}}_repo.create = AsyncMock(return_value=created)

        dto = {{Name}}CreateDTO({{unique_field}}="test_{{unique_field}}", isActive=1)
        result = await {{name}}_service.create_{{name}}(dto)

        assert result.{{unique_field}} == "test_{{unique_field}}"

    @pytest.mark.asyncio
    async def test_create_{{name}}_duplicate(self, {{name}}_service, mock_{{name}}_repo):
        """测试创建{{chinese_name}}时{{unique_field_cn}}重复。"""
        existing = {{Name}}({{unique_field}}="test_{{unique_field}}")
        mock_{{name}}_repo.get_by_{{unique_field}} = AsyncMock(return_value=existing)

        dto = {{Name}}CreateDTO({{unique_field}}="test_{{unique_field}}")
        with pytest.raises(ConflictError) as exc_info:
            await {{name}}_service.create_{{name}}(dto)
        assert "已存在" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_{{name}}_not_found(self, {{name}}_service, mock_{{name}}_repo):
        """测试获取不存在的{{chinese_name}}。"""
        mock_{{name}}_repo.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(NotFoundError):
            await {{name}}_service.get_{{name}}("non-existent-id")

{{pagination_test_if_applicable}}
    @pytest.mark.asyncio
    async def test_update_{{name}}_success(self, {{name}}_service, mock_{{name}}_repo, mock_session):
        """测试更新{{chinese_name}}成功。"""
        existing = {{Name}}(id="test-id-1", {{unique_field}}="old_value", is_active=1)
        mock_{{name}}_repo.get_by_id = AsyncMock(return_value=existing)
        updated = {{Name}}(id="test-id-1", {{unique_field}}="new_value", is_active=1)
        mock_{{name}}_repo.update = AsyncMock(return_value=updated)

        dto = {{Name}}UpdateDTO({{unique_field}}="new_value")
        result = await {{name}}_service.update_{{name}}("test-id-1", dto)

        mock_{{name}}_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_{{name}}_not_found(self, {{name}}_service, mock_{{name}}_repo):
        """测试更新不存在的{{chinese_name}}。"""
        mock_{{name}}_repo.get_by_id = AsyncMock(return_value=None)

        dto = {{Name}}UpdateDTO({{unique_field}}="new_value")
        with pytest.raises(NotFoundError):
            await {{name}}_service.update_{{name}}("non-existent-id", dto)

    @pytest.mark.asyncio
    async def test_delete_{{name}}_success(self, {{name}}_service, mock_{{name}}_repo):
        """测试删除{{chinese_name}}成功。"""
        mock_{{name}}_repo.delete = AsyncMock(return_value=True)

        result = await {{name}}_service.delete_{{name}}("test-id-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_{{name}}_not_found(self, {{name}}_service, mock_{{name}}_repo):
        """测试删除不存在的{{chinese_name}}。"""
        mock_{{name}}_repo.delete = AsyncMock(return_value=False)

        with pytest.raises(NotFoundError):
            await {{name}}_service.delete_{{name}}("non-existent-id")
```

分页模式追加测试：
```python
    @pytest.mark.asyncio
    async def test_get_{{name}}s_with_pagination(self, {{name}}_service, mock_{{name}}_repo):
        """测试获取{{chinese_name}}列表（分页+筛选）。"""
        items = [{{Name}}(id="1", {{unique_field}}="item1", is_active=1), {{Name}}(id="2", {{unique_field}}="item2", is_active=1)]
        mock_{{name}}_repo.count = AsyncMock(return_value=2)
        mock_{{name}}_repo.get_all = AsyncMock(return_value=items)

        query = {{Name}}ListQueryDTO(pageNum=1, pageSize=10)
        results, total = await {{name}}_service.get_{{name}}s(query)

        assert total == 2
        assert len(results) == 2
        mock_{{name}}_repo.count.assert_called_once()
        mock_{{name}}_repo.get_all.assert_called_once()
```

---

## 前端模板

### 11. API 类 (`web/src/api/system/{{name}}.ts`)

**分页模式**：

```typescript
import { http } from "@/utils/http";
import { BaseApi, type Result, type ResultTable } from "../base";

class {{Name}}Api extends BaseApi {
  constructor() {
    super("/{{name}}");
  }

  /** 获取{{chinese_name}}列表（分页） — 覆写父类list，使用ResultTable */
  list<T = any>(params?: object): Promise<ResultTable<T>> {
    return http.request<ResultTable<T>>("post", this.prefix, { data: params });
  }
}

export const {{name}}Api = new {{Name}}Api();
```

**树形模式**：

```typescript
import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";

class {{Name}}Api extends BaseApi {
  constructor() {
    super("/{{name}}");
  }

  /** 获取{{chinese_name}}列表（树结构，不分页） */
  list<T = any>(params?: object): Promise<Result<T>> {
    return http.request<Result<T>>("post", this.prefix, { data: params });
  }
}

export const {{name}}Api = new {{Name}}Api();
```

### 12. 前端视图文件

#### 类型定义 (`web/src/views/system/{{name}}/utils/types.ts`)

```typescript
interface FormItemProps {
{{fields_form_item_props}}
  isActive: number;
  description: string;
}
interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
```

字段映射：`str → string`, `int → number`, `str|None → string | number`, `parentId → parentId: number`

#### 校验规则 (`web/src/views/system/{{name}}/utils/rule.ts`)

```typescript
import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
{{required_field_rules}}
});
```

必填字段生成规则：`{ fieldName: [{ required: true, message: "{{字段中文名}}为必填项", trigger: "blur" }] }`

#### 核心 Hook (`web/src/views/system/{{name}}/utils/hook.tsx`)

**分页模式**：

```typescript
import dayjs from "dayjs";
import editForm from "../form.vue";
import { message } from "@/utils/message";
import { ElMessageBox } from "element-plus";
import { usePublicHooks } from "../../hooks";
import { addDialog } from "@/components/ReDialog";
import type { FormItemProps } from "../utils/types";
import type { PaginationProps } from "@pureadmin/table";
import { deviceDetection } from "@pureadmin/utils";
import { {{name}}Api } from "@/api/system/{{name}}";
import { type Ref, reactive, ref, onMounted, h, toRaw } from "vue";

export function use{{Name}}() {
  const form = reactive({
{{search_form_fields}}
  });
  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const switchLoadMap = ref({});
  const { switchStyle } = usePublicHooks();
  const pagination = reactive<PaginationProps>({
    total: 0,
    pageSize: 10,
    currentPage: 1,
    background: true
  });
  const columns: TableColumnList = [
{{table_columns_definition}}
    {
      label: "状态",
      prop: "isActive",
      minWidth: 90,
      cellRenderer: scope => (
        <el-switch
          size={scope.props.size === "small" ? "small" : "default"}
          loading={switchLoadMap.value[scope.index]?.loading}
          v-model={scope.row.isActive}
          active-value={1}
          inactive-value={0}
          active-text="已启用"
          inactive-text="已停用"
          inline-prompt
          style={switchStyle.value}
          onChange={() => onChange(scope as any)}
        />
      )
    },
    {
      label: "创建时间",
      minWidth: 160,
      prop: "createdTime",
      formatter: ({ createdTime }) =>
        createdTime ? dayjs(createdTime).format("YYYY-MM-DD HH:mm:ss") : "-"
    },
    {
      label: "操作",
      fixed: "right",
      width: 180,
      slot: "operation"
    }
  ];

  function onChange({ row, index }) {
    ElMessageBox.confirm(
      `确认要<strong>${!row.isActive ? "停用" : "启用"}</strong><strong style='color:var(--el-color-primary)'>${row.{{display_field}}}</strong>吗?`,
      "系统提示",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning", dangerouslyUseHTMLString: true, draggable: true }
    )
      .then(async () => {
        switchLoadMap.value[index] = Object.assign({}, switchLoadMap.value[index], { loading: true });
        try {
          const { code } = await {{name}}Api.updateStatus(row.id, { isActive: row.isActive });
          if (code === 0) {
            message(`已${row.isActive ? "启用" : "停用"}${row.{{display_field}}}`, { type: "success" });
          }
        } catch (error) {
          row.isActive = row.isActive === 1 ? 0 : 1;
          message("修改状态失败", { type: "error" });
        } finally {
          switchLoadMap.value[index] = Object.assign({}, switchLoadMap.value[index], { loading: false });
        }
      })
      .catch(() => { row.isActive = row.isActive === 1 ? 0 : 1; });
  }

  function handleDelete(row) {
    ElMessageBox.confirm(
      `确认要删除{{chinese_name}} <strong style='color:var(--el-color-primary)'>${row.{{display_field}}}</strong> 吗?`,
      "系统提示",
      { confirmButtonText: "确定", cancelButtonText: "取消", type: "warning", dangerouslyUseHTMLString: true, draggable: true }
    )
      .then(async () => {
        const { code } = await {{name}}Api.destroy(row.id);
        if (code === 0) {
          message(`已成功删除{{chinese_name}} ${row.{{display_field}}}`, { type: "success" });
          onSearch();
        }
      })
      .catch(() => {});
  }

  function handleSizeChange(val: number) { console.log(`${val} items per page`); }
  function handleCurrentChange(val: number) { console.log(`current page: ${val}`); }
  function handleSelectionChange(val) { console.log("handleSelectionChange", val); }

  async function onSearch() {
    loading.value = true;
    const { code, data } = await {{name}}Api.list(toRaw(form));
    if (code === 0) {
      dataList.value = data.list;
      pagination.total = data.total;
      pagination.pageSize = data.pageSize;
      pagination.currentPage = data.currentPage;
    }
    setTimeout(() => { loading.value = false; }, 500);
  }

  const resetForm = formEl => {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  };

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}{{chinese_name}}`,
      props: {
        formInline: {
{{dialog_form_fields}}
          isActive: row?.isActive ?? 1,
          description: row?.description ?? ""
        }
      },
      width: "40%",
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () => h(editForm, { ref: formRef, formInline: null }),
      beforeSure: (done, { options }) => {
        const FormRef = formRef.value.getRef();
        const curData = options.props.formInline as FormItemProps;

        FormRef.validate(async valid => {
          if (valid) {
            try {
              const payload = {
{{payload_fields}}
                isActive: curData.isActive,
                description: curData.description || null
              };

              if (title === "新增") {
                const { code } = await {{name}}Api.create(payload);
                if (code === 0 || code === 201) {
                  message(`成功创建{{chinese_name}} ${curData.{{display_field}}}`, { type: "success" });
                  done();
                  onSearch();
                }
              } else {
                const { code } = await {{name}}Api.partialUpdate(row.id, payload);
                if (code === 0) {
                  message(`成功更新{{chinese_name}} ${curData.{{display_field}}}`, { type: "success" });
                  done();
                  onSearch();
                }
              }
            } catch (error) {
              message(`${title}{{chinese_name}}失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  onMounted(() => { onSearch(); });

  return {
    form, loading, columns, dataList, pagination,
    onSearch, resetForm, openDialog, handleDelete,
    handleSizeChange, handleCurrentChange, handleSelectionChange
  };
}
```

**树形模式** 差异：
- `onSearch` 使用 `handleTree(data)` 转换，无分页
- `columns` 中添加 `parentId` 显示
- `openDialog` 中支持 `parentId` 传递
- 删除操作前确认无子节点

#### 表单组件 (`web/src/views/system/{{name}}/form.vue`)

```vue
<script setup lang="ts">
import { ref } from "vue";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
{{form_default_values}}
    isActive: 1,
    description: ""
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);

function getRef() {
  return ruleFormRef.value;
}

defineExpose({ getRef });
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="newFormInline"
    :rules="formRules"
    label-width="82px"
  >
{{form_items_template}}
    <el-form-item label="状态">
      <el-switch
        v-model="newFormInline.isActive"
        :active-value="1"
        :inactive-value="0"
        inline-prompt
        active-text="启用"
        inactive-text="停用"
      />
    </el-form-item>

    <el-form-item label="描述">
      <el-input
        v-model="newFormInline.description"
        placeholder="请输入描述信息"
        type="textarea"
      />
    </el-form-item>
  </el-form>
</template>
```

**字段到表单组件映射**：
- `str` (短文本) → `<el-input v-model="newFormInline.fieldName" clearable placeholder="请输入{{字段中文名}}" />`
- `str` (长文本) → `<el-input v-model="newFormInline.fieldName" placeholder="请输入{{字段中文名}}" type="textarea" />`
- `int` → `<el-input-number v-model="newFormInline.fieldName" class="w-full!" :min="0" controls-position="right" />`
- `float` → `<el-input-number v-model="newFormInline.fieldName" class="w-full!" :min="0" :precision="2" controls-position="right" />`
- `is_active` → `<el-switch>` (已内置于模板)
- `parent_id` → `<el-cascader>` (树形模式)
- `description` → `<el-input type="textarea">` (已内置于模板)

#### 主页面 (`web/src/views/system/{{name}}/index.vue`)

**分页模式**：

```vue
<script setup lang="ts">
import { ref } from "vue";
import { use{{Name}} } from "./utils/hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "System{{Name}}"
});

const formRef = ref();
const tableRef = ref();

const {
  form, loading, columns, dataList, pagination,
  onSearch, resetForm, openDialog, handleDelete,
  handleSizeChange, handleCurrentChange, handleSelectionChange
} = use{{Name}}();
</script>

<template>
  <div class="main">
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
    >
{{search_form_items}}
      <el-form-item>
        <el-button
          type="primary"
          :icon="useRenderIcon('ri/search-line')"
          :loading="loading"
          @click="onSearch"
        >搜索</el-button>
        <el-button :icon="useRenderIcon(Refresh)" @click="resetForm(formRef)">重置</el-button>
      </el-form-item>
    </el-form>

    <PureTableBar
      title="{{chinese_name}}管理"
      :columns="columns"
      @refresh="onSearch"
    >
      <template #buttons>
        <el-button
          type="primary"
          :icon="useRenderIcon(AddFill)"
          @click="openDialog()"
        >新增{{chinese_name}}</el-button>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <pure-table
          ref="tableRef"
          align-whole="center"
          showOverflowTooltip
          table-layout="auto"
          :loading="loading"
          :size="size"
          adaptive
          :adaptiveConfig="{ offsetBottom: 108 }"
          :data="dataList"
          :columns="dynamicColumns"
          :pagination="{ ...pagination, size }"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @selection-change="handleSelectionChange"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        >
          <template #operation="{ row }">
            <el-button
              class="reset-margin"
              link
              type="primary"
              :size="size"
              :icon="useRenderIcon(EditPen)"
              @click="openDialog('修改', row)"
            >修改</el-button>
            <el-popconfirm
              :title="`是否确认删除{{chinese_name}}名称为${row.{{display_field}}}的这条数据`"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
                  class="reset-margin"
                  link
                  type="primary"
                  :size="size"
                  :icon="useRenderIcon(Delete)"
                >删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </pure-table>
      </template>
    </PureTableBar>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}

.main-content {
  margin: 24px 24px 0 !important;
}

.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
</style>
```

### 13. 前端模块注册

修改 `web/src/api/system.ts`，追加函数式导出：

```typescript
// 追加到文件中
import { {{name}}Api } from "./system/{{name}}";
export const get{{Name}}List = (data?: object) => {{name}}Api.list(data);
export const create{{Name}} = (data?: object) => {{name}}Api.create(data);
export const update{{Name}} = (id: string, data?: object) => {{name}}Api.partialUpdate(id, data);
export const delete{{Name}} = (id: string) => {{name}}Api.destroy(id);
```

---

## 验证清单

代码生成后，按以下顺序验证：

### 后端验证

1. **代码规范检查**：
   ```bash
   cd service
   ruff check . --fix && ruff format .
   ```

2. **单元测试**：
   ```bash
   pytest tests/unit/test_{{name}}_service.py -v
   ```

3. **类型检查**（可选）：
   ```bash
   mypy src/
   ```

4. **启动后端服务确认无导入错误**：
   ```bash
   python -m scripts.cli runserver
   ```
   访问 `http://localhost:8000/api/docs` 确认新 API 出现在 Swagger UI 中

### 前端验证

5. **编译检查**：
   ```bash
   cd web
   pnpm build
   ```

6. **前端开发服务器**：
   ```bash
   pnpm dev
   ```

### 前后端联调验证

7. **使用 Playwright 浏览器自动化**：
   - 启动前后端服务
   - 登录系统
   - 导航到新模块页面（需先在后端菜单数据中注册）
   - 测试列表加载
   - 测试新增功能
   - 测试编辑功能
   - 测试删除功能
   - 验证搜索/筛选功能

### 注意事项

- 生成代码时严格遵循现有模块的代码风格
- `__init__.py` 修改时保持原有导出顺序和格式，仅追加新条目
- 所有中文注释，与项目约定一致
- DTO 字段命名使用 camelCase（前端约定），Python 内部使用 snake_case
- 树形结构通过 `parent_id` 字段自动识别
- 确保后端服务 (`localhost:8000`) 和前端服务 (`localhost:8848`) 同时运行才能联调
- 前端路由由后端菜单 API 动态驱动，新模块需要管理员在菜单管理中配置对应菜单项
