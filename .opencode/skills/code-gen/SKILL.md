---
name: code-gen
description: 根据 MySQL 表定义，自动生成后端 DDD 四层代码和前端 Vue3 页面，支持标准 REST 增删改查。
license: MIT
---

## 什么时候用我

当你需要为一个新的 MySQL 数据表快速生成完整 CRUD 功能时。你只需要提供 CREATE TABLE 定义，我会自动分析字段并生成：
- **后端**：领域实体 → 仓储接口 → DTO → 应用服务 → ORM 模型 → 仓储实现 → API 路由 → 依赖注入
- **前端**：API 类 → Vue 页面 → 表单组件 → Hook → 类型定义 → 校验规则

## 输入格式

提供 MySQL CREATE TABLE 语句，例如：

```sql
CREATE TABLE `sys_xxx` (
  `id` varchar(32) NOT NULL,
  `name` varchar(128) NOT NULL COMMENT '名称',
  `code` varchar(64) DEFAULT NULL COMMENT '编码',
  `rank` int DEFAULT 0 COMMENT '排序号',
  `is_active` int DEFAULT 1 COMMENT '是否启用',
  `creator_id` varchar(150) DEFAULT NULL COMMENT '创建人ID',
  `modifier_id` varchar(150) DEFAULT NULL COMMENT '修改人ID',
  `parent_id` varchar(32) DEFAULT NULL COMMENT '父级ID',
  `created_time` datetime DEFAULT NULL COMMENT '创建时间',
  `updated_time` datetime DEFAULT NULL COMMENT '更新时间',
  `description` varchar(256) DEFAULT NULL COMMENT '描述',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin COMMENT='XXX表';
```

## 开发顺序

1. **后端**（按此顺序生成所有文件）
2. **前端**（按此顺序生成所有文件）

每生成一个文件后，检查代码风格是否与现有代码一致。

---

## 第一步：分析表定义

从 CREATE TABLE 中提取：
- **表名**：去掉 `sys_` 前缀获取实体名（如 `sys_departments` → `department`）
- **主键**：通常为 `id`（32位UUID字符串）
- **字段列表**：每个字段的名称、类型、是否必填、默认值、注释
- **业务字段**：排除通用字段（`id`, `creator_id`, `modifier_id`, `parent_id`, `created_time`, `updated_time`）后剩余的字段
- **唯一字段**：有 UNIQUE 约束的字段
- **父子关系**：如果包含 `parent_id` 且自引用，说明是树形结构

### 类型映射规则（后端 Python）

| MySQL 类型 | Python 类型 | DTO 类型 |
|-----------|------------|----------|
| varchar/char | str | str |
| int/tinyint/smallint | int | int |
| bigint | int | int |
| decimal/float/double | Decimal/float | float |
| datetime/timestamp | datetime \| None | datetime \| None |
| text | str \| None | str \| None |

### 字段命名映射（后端）

| MySQL 列名 | Python/实体字段 | DTO 字段 | 前端字段 |
|-----------|----------------|----------|---------|
| `name` | `name` | `name` | `name` |
| `is_active` | `is_active` | `isActive` | `isActive` |
| `created_time` | `created_time` | `createdTime` | `createdTime` |
| `parent_id` | `parent_id` | `parentId` | `parentId` |
| `mode_type` | `mode_type` | `modeType` | `modeType` |
| `auto_bind` | `auto_bind` | `autoBind` | `autoBind` |

### 类型映射规则（前端 TypeScript）

| MySQL 类型 | TypeScript 类型 | 表单组件 |
|-----------|----------------|---------|
| varchar/char | string | el-input |
| int/tinyint 且字段名含 `is_`/`status` | number (0/1) | el-switch (active-value=1, inactive-value=0) |
| int (排序号) | number | el-input-number (min=0 / max=9999) |
| int (其他) | number | el-input-number |
| datetime | string | 只读显示 |
| text | string | el-input type="textarea" |
| decimal | number | el-input-number |

---

## 第二步：后端代码生成

所有后端代码放在 `service/src/` 目录下。

### 2.1 领域实体 — `service/src/domain/entities/{entity}.py`

模板（参考 `service/src/domain/entities/department.py`）：

```python
"""${模块注释}领域实体。"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ${Entity}Entity:
    """${模块注释}领域实体。"""

    id: str
    ${domain_fields}
    creator_id: str | None = None
    modifier_id: str | None = None
    ${parent_id_field}
    created_time: datetime | None = None
    updated_time: datetime | None = None
    description: str | None = None

    # ---- 状态查询属性 ----

    @property
    def is_active_${entity}(self) -> bool:
        """是否启用。"""
        return self.is_active == 1

    # ---- 更新方法 ----

    def update_info(self, *, ${update_params}) -> None:
        """有条件地更新${模块注释}信息。"""
        ${update_body}

    # ---- 工厂方法 ----

    @classmethod
    def create_new(cls, ${create_params}) -> ${Entity}Entity:
        """创建新${模块注释}实体的工厂方法。"""
        return cls(
            id=uuid.uuid4().hex,
            ${create_body}
        )
```

**规则**：
- 每个业务字段在 `update_info` 中都需要 `if X is not None: self.X = X`
- `create_new` 的入参不包括 `id`、`creator_id`、`modifier_id`、`created_time`、`updated_time`、`description`
- `parent_id` 只在表有 `parent_id` 字段时才包含
- `is_active` 字段在 `create_new` 中不传参，新建时默认通过 `is_active=is_active` 参数传入

### 2.2 仓储接口 — `service/src/domain/repositories/{entity}_repository.py`

模板（参考 `service/src/domain/repositories/department_repository.py`）：

```python
"""${模块注释}领域 - 仓储接口。"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from src.domain.entities.${entity} import ${Entity}Entity

if TYPE_CHECKING:
    from sqlmodel.ext.asyncio.session import AsyncSession


class ${Entity}RepositoryInterface(ABC):
    """${模块注释}的抽象仓储接口。"""

    @abstractmethod
    def __init__(self, session: "AsyncSession") -> None:
        ...

    @abstractmethod
    async def get_all(self) -> list[${Entity}Entity]:
        ...

    @abstractmethod
    async def get_by_id(self, ${entity}_id: str) -> ${Entity}Entity | None:
        ...

    @abstractmethod
    async def get_by_name(self, name: str) -> ${Entity}Entity | None:
        ...

    @abstractmethod
    async def create(self, ${entity}: ${Entity}Entity) -> ${Entity}Entity:
        ...

    @abstractmethod
    async def update(self, ${entity}: ${Entity}Entity) -> ${Entity}Entity:
        ...

    @abstractmethod
    async def delete(self, ${entity}_id: str) -> bool:
        ...

    @abstractmethod
    async def count(self, ${count_params}) -> int:
        ...

    @abstractmethod
    async def get_filtered(self, ${filter_params}) -> list[${Entity}Entity]:
        ...
```

**规则**：
- 如果表有 `code` 字段（唯一），添加 `get_by_code` 方法
- 如果表有 `parent_id` 字段，添加 `get_by_parent_id` 方法
- `get_filtered` 支持查询参数过滤（名称模糊匹配、状态过滤等）

### 2.3 DTO — `service/src/application/dto/{entity}_dto.py`

模板（参考 `service/src/application/dto/department_dto.py`）：

```python
"""应用层 - ${模块注释}领域的数据传输对象。"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from src.application.validators import empty_str_to_none, normalize_optional_id


class ${Entity}CreateDTO(BaseModel):
    """创建${模块注释}请求"""
    ${create_dto_fields}

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | None) -> str | None:
        return normalize_optional_id(v)

    @field_validator("description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        return empty_str_to_none(v)

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_status(cls, v: int | str | None) -> int:
        if v == "" or v is None:
            return 1
        return int(v) if isinstance(v, str) else v


class ${Entity}UpdateDTO(BaseModel):
    """更新${模块注释}请求"""
    ${update_dto_fields}

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | None) -> str | None:
        return normalize_optional_id(v)

    @field_validator("name", "description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        return empty_str_to_none(v)


class ${Entity}ResponseDTO(BaseModel):
    """${模块注释}响应"""
    id: str
    ${response_dto_fields}
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class ${Entity}ListQueryDTO(BaseModel):
    """${模块注释}列表查询请求"""
    ${query_dto_fields}
```

**规则**：
- `CreateDTO` 中业务字段为必填（`name`）或带默认值
- `UpdateDTO` 中所有业务字段为 `None | None = Field(default=None)`
- `ResponseDTO` 使用驼峰命名，`model_config = {"from_attributes": True}`
- `ListQueryDTO` 包含查询参数（如 `name`, `isActive`）
- 对 `parentId` 字段使用 `normalize_optional_id` 验证器
- 对 `isActive` 在 CreateDTO 中默认 `1`，空字符串转为 `1`

### 2.4 应用服务 — `service/src/application/services/{entity}_service.py`

模板（参考 `service/src/application/services/department_service.py`）：

```python
"""应用层 - ${模块注释}服务。"""

from src.application.dto.${entity}_dto import (
    ${Entity}CreateDTO,
    ${Entity}ListQueryDTO,
    ${Entity}ResponseDTO,
    ${Entity}UpdateDTO,
)
from src.domain.entities.${entity} import ${Entity}Entity
from src.domain.exceptions import BusinessError, ConflictError, NotFoundError
from src.domain.repositories.${entity}_repository import ${Entity}RepositoryInterface


class ${Entity}Service:
    """${模块注释}领域操作的应用服务。"""

    def __init__(self, ${entity}_repo: ${Entity}RepositoryInterface):
        self.${entity}_repo = ${entity}_repo

    async def get_${entity}s(self, query: ${Entity}ListQueryDTO) -> list[${Entity}ResponseDTO]:
        """获取${模块注释}列表。"""
        ${entities} = await self.${entity}_repo.get_filtered(${service_filter_args})
        return [self._to_response(d) for d in ${entities}]

    async def create_${entity}(self, dto: ${Entity}CreateDTO) -> ${Entity}ResponseDTO:
        """创建${模块注释}。"""
        existing = await self.${entity}_repo.get_by_name(dto.name)
        if existing:
            raise ConflictError("${模块注释}名称已存在")

        ${entity} = ${Entity}Entity.create_new(
            ${create_service_args}
        )
        ${entity}.is_active = dto.isActive

        created = await self.${entity}_repo.create(${entity})
        return self._to_response(created)

    async def update_${entity}(self, ${entity}_id: str, dto: ${Entity}UpdateDTO) -> ${Entity}ResponseDTO:
        """更新${模块注释}。"""
        ${entity} = await self.${entity}_repo.get_by_id(${entity}_id)
        if not ${entity}:
            raise NotFoundError("${模块注释}不存在")

        ${entity}.update_info(${update_service_args})
        if dto.isActive is not None:
            ${entity}.is_active = dto.isActive

        updated = await self.${entity}_repo.update(${entity})
        return self._to_response(updated)

    async def delete_${entity}(self, ${entity}_id: str) -> bool:
        """删除${模块注释}。"""
        ${entity} = await self.${entity}_repo.get_by_id(${entity}_id)
        if not ${entity}:
            raise NotFoundError("${模块注释}不存在")

        ${delete_extra_logic}
        return await self.${entity}_repo.delete(${entity}_id)

    @staticmethod
    def _to_response(${entity}: ${Entity}Entity) -> ${Entity}ResponseDTO:
        """将${模块注释}实体转换为响应 DTO。"""
        return ${Entity}ResponseDTO(
            id=${entity}.id,
            ${to_response_fields}
        )
```

**规则**：
- 如果表有 `code` 字段且唯一，在 `create` 中检查 code 唯一性
- 如果表有 `parent_id`，在 `create` 中验证父级存在，在 `update` 中处理 `parentId` 和循环引用
- 树形结构需要添加 `get_tree` 方法和 `_build_tree` 方法

### 2.5 ORM 模型 — `service/src/infrastructure/database/models/{entity}.py`

模板（参考 `service/src/infrastructure/database/models/department.py`）：

```python
"""${模块注释}实体模型。"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, func
from sqlmodel import Field, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.${entity} import ${Entity}Entity


class ${Entity}(SQLModel, table=True):
    """${模块注释}实体。"""

    __tablename__ = "${table_name}"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, max_length=32)
    ${orm_fields}
    creator_id: str | None = Field(default=None, max_length=150)
    modifier_id: str | None = Field(default=None, max_length=150)
    ${orm_parent_id_field}
    created_time: datetime | None = Field(default=None, sa_column=Column(DateTime(6), server_default=func.now()))
    updated_time: datetime | None = Field(
        default=None, sa_column=Column(DateTime(6), server_default=func.now(), onupdate=func.now())
    )
    description: str | None = Field(default=None, max_length=256)

    def to_domain(self) -> "${Entity}Entity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.${entity} import ${Entity}Entity

        return ${Entity}Entity(
            id=self.id,
            ${to_domain_fields}
        )

    @classmethod
    def from_domain(cls, entity: "${Entity}Entity") -> "${Entity}":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            ${from_domain_fields}
        )

    def __repr__(self) -> str:
        return f"<${Entity}(id={self.id}, name={self.name})>"
```

**字段映射规则**（ORM 模型字段定义）：
- `varchar` → `str | None = Field(default=None, max_length=N)` 或 `str = Field(max_length=N)`（必填）
- `int` → `int = Field(default=0)` 或 `int | None = Field(default=None)`
- `tinyint(1)` → `int = Field(default=1)`（布尔型用 int）
- `datetime` → `datetime | None = Field(default=None)`
- `text` → `str | None = Field(default=None)`
- 唯一约束 → `Field(..., unique=True)`

### 2.6 仓储实现 — `service/src/infrastructure/repositories/{entity}_repository.py`

模板（参考 `service/src/infrastructure/repositories/department_repository.py`）：

```python
"""使用 SQLModel 和 FastCRUD 实现的${模块注释}仓库。"""

from typing import Any

from fastcrud import FastCRUD
from sqlmodel.ext.asyncio.session import AsyncSession

from src.domain.entities.${entity} import ${Entity}Entity
from src.domain.repositories.${entity}_repository import ${Entity}RepositoryInterface
from src.infrastructure.database.models import ${Entity}


class ${Entity}Repository(${Entity}RepositoryInterface):
    """${模块注释}仓储的 SQLModel 实现，使用 FastCRUD 简化 CRUD 操作。"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._crud = FastCRUD(${Entity})

    async def get_all(self) -> list[${Entity}Entity]:
        result = await self._crud.get_multi(
            self.session, schema_to_select=${Entity}, return_as_model=True, return_total_count=False
        )
        raw = result.get("data", [])
        return [d.to_domain() for d in raw]

    async def get_by_id(self, ${entity}_id: str) -> ${Entity}Entity | None:
        model = await self._crud.get(
            self.session, id=${entity}_id, schema_to_select=${Entity}, return_as_model=True
        )
        return model.to_domain() if model else None

    async def get_by_name(self, name: str) -> ${Entity}Entity | None:
        model = await self._crud.get(
            self.session, name=name, schema_to_select=${Entity}, return_as_model=True
        )
        return model.to_domain() if model else None

    ${extra_repo_methods}

    async def create(self, ${entity}: ${Entity}Entity) -> ${Entity}Entity:
        model = ${Entity}.from_domain(${entity})
        self.session.add(model)
        await self.session.flush()
        loaded = await self.get_by_id(model.id)
        return loaded  # type: ignore[return-value]

    async def update(self, ${entity}: ${Entity}Entity) -> ${Entity}Entity:
        from sqlalchemy import update as sa_update

        stmt = (
            sa_update(${Entity})
            .where(${Entity}.id == ${entity}.id)
            .values(
                ${update_values}
            )
        )
        await self.session.exec(stmt)  # type: ignore[arg-type]
        await self.session.flush()
        updated = await self.get_by_id(${entity}.id)
        return updated  # type: ignore[return-value]

    async def delete(self, ${entity}_id: str) -> bool:
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(${Entity}).where(${Entity}.id == ${entity}_id)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def count(self, ${count_impl_params}) -> int:
        filters: dict[str, Any] = {}
        ${count_filters}
        return await self._crud.count(self.session, **filters)

    async def get_filtered(self, ${filter_impl_params}) -> list[${Entity}Entity]:
        from sqlalchemy import select

        stmt = select(${Entity})
        ${where_clauses}
        ${order_clause}

        result = await self.session.execute(stmt)
        return [d.to_domain() for d in result.scalars().all()]
```

### 2.7 API 路由 — `service/src/api/v1/{entity}_router.py`

模板（参考 `service/src/api/v1/dept_router.py`）：

```python
"""${模块注释}管理路由模块。"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Body, Depends

from src.api.common import success_response
from src.api.dependencies import get_${entity}_service, require_permission
from src.application.dto.${entity}_dto import ${Entity}CreateDTO, ${Entity}ListQueryDTO, ${Entity}UpdateDTO
from src.application.services.${entity}_service import ${Entity}Service


class ${Entity}Router(Routable):
    """${模块注释}管理路由类。"""

    @post("/${entity}")
    async def get_${entity}_list(
        self,
        data: dict = Body(default={}),
        service: ${Entity}Service = Depends(get_${entity}_service),
        _: dict = Depends(require_permission("${entity}:view")),
    ) -> dict:
        """获取${模块注释}列表。"""
        query = ${Entity}ListQueryDTO(${list_query_args})
        ${entities} = await service.get_${entity}s(query)
        ${entity}_list = [d.model_dump() for d in ${entities}]
        return success_response(data=${entity}_list)

    @post("/${entity}/create")
    async def create_${entity}(
        self,
        dto: ${Entity}CreateDTO,
        service: ${Entity}Service = Depends(get_${entity}_service),
        _: dict = Depends(require_permission("${entity}:add")),
    ) -> dict:
        """创建${模块注释}。"""
        ${entity} = await service.create_${entity}(dto)
        return success_response(data={"id": ${entity}.id, "name": ${entity}.name}, message="创建成功", code=201)

    @put("/${entity}/{${entity}_id}")
    async def update_${entity}(
        self,
        ${entity}_id: str,
        dto: ${Entity}UpdateDTO,
        service: ${Entity}Service = Depends(get_${entity}_service),
        _: dict = Depends(require_permission("${entity}:edit")),
    ) -> dict:
        """更新${模块注释}。"""
        ${entity} = await service.update_${entity}(${entity}_id, dto)
        return success_response(data={"id": ${entity}.id, "name": ${entity}.name}, message="更新成功")

    @delete("/${entity}/{${entity}_id}")
    async def delete_${entity}(
        self,
        ${entity}_id: str,
        service: ${Entity}Service = Depends(get_${entity}_service),
        _: dict = Depends(require_permission("${entity}:delete")),
    ) -> dict:
        """删除${模块注释}。"""
        await service.delete_${entity}(${entity}_id)
        return success_response(message="删除成功")

    ${tree_endpoint}
```

### 2.8 DI 工厂 — `service/src/api/dependencies/{entity}_service.py`

模板（参考 `service/src/api/dependencies/department_service.py`）：

```python
"""${模块注释}应用服务工厂。"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.application.services.${entity}_service import ${Entity}Service
from src.infrastructure.database import get_db
from src.infrastructure.repositories.${entity}_repository import ${Entity}Repository


async def get_${entity}_service(db: AsyncSession = Depends(get_db)) -> ${Entity}Service:
    """获取${模块注释}服务实例。"""
    ${entity}_repo = ${Entity}Repository(db)
    return ${Entity}Service(${entity}_repo=${entity}_repo)
```

### 2.9 更新所有 `__init__.py`

需要修改以下文件的 `__init__.py`：

| 文件 | 添加内容 |
|------|---------|
| `src/domain/entities/__init__.py` | `from src.domain.entities.${entity} import ${Entity}Entity` + `__all__` 添加 |
| `src/domain/repositories/__init__.py` | `from src.domain.repositories.${entity}_repository import ${Entity}RepositoryInterface` + `__all__` 添加 |
| `src/application/dto/__init__.py` | 导入四个 DTO 类 + `__all__` 添加 |
| `src/application/services/__init__.py` | `from src.application.services.${entity}_service import ${Entity}Service` + `__all__` 添加 |
| `src/infrastructure/database/models/__init__.py` | `from src.infrastructure.database.models.${entity} import ${Entity}` + `__all__` 添加 |
| `src/infrastructure/repositories/__init__.py` | `from src.infrastructure.repositories.${entity}_repository import ${Entity}Repository` + `__all__` 添加 |
| `src/api/v1/__init__.py` | 导入 Router 类 + `system_router.include_router(${Entity}Router().router, tags=["${模块注释}管理"])` |
| `src/api/dependencies/__init__.py` | 导入 factory 函数 + `__all__` 添加 |

### 2.10 后端生成顺序总表

按这个顺序逐个生成文件，每生成一个后立即更新对应的 `__init__.py`：

```
1  →  service/src/domain/entities/{entity}.py
2  →  service/src/domain/entities/__init__.py (更新)
3  →  service/src/domain/repositories/{entity}_repository.py
4  →  service/src/domain/repositories/__init__.py (更新)
5  →  service/src/application/dto/{entity}_dto.py
6  →  service/src/application/dto/__init__.py (更新)
7  →  service/src/application/services/{entity}_service.py
8  →  service/src/application/services/__init__.py (更新)
9  →  service/src/infrastructure/database/models/{entity}.py
10 →  service/src/infrastructure/database/models/__init__.py (更新)
11 →  service/src/infrastructure/repositories/{entity}_repository.py
12 →  service/src/infrastructure/repositories/__init__.py (更新)
13 →  service/src/api/dependencies/{entity}_service.py
14 →  service/src/api/dependencies/__init__.py (更新)
15 →  service/src/api/v1/{entity}_router.py
16 →  service/src/api/v1/__init__.py (更新)
```

---

## 第三步：前端代码生成

所有前端代码放在 `web/src/` 目录下。

### 3.1 API 类 — `web/src/api/system/{entity}.ts`

模板（参考 `web/src/api/system/dept.ts`）：

```typescript
import { http } from "@/utils/http";
import { BaseApi, type Result } from "../base";

class ${Entity}Api extends BaseApi {
  constructor() {
    super("/${entity}");
  }
}

export const ${entity}Api = new ${Entity}Api();
```

**规则**：
- 如果是列表（非分页树），覆写 `list` 方法使用 `post` 请求并返回 `Result<T>`（而非 `ResultTable<T>`）
- 如果是分页列表，直接使用基类方法（`post` 请求返回 `ResultTable<T>`）

### 3.2 更新 API 兼容层 — `web/src/api/system.ts`

在 `web/src/api/system.ts` 末尾添加：

```typescript
// =============================================================================
// ${模块注释}管理 — 委托给 ${Entity}Api
// =============================================================================

import { ${entity}Api } from "./system/${entity}";

/** 获取${模块注释}列表 */
export const get${Entity}List = (data?: object) => ${entity}Api.list(data);

/** 创建${模块注释} */
export const create${Entity} = (data?: object) => ${entity}Api.create(data);

/** 更新${模块注释} */
export const update${Entity} = (id: string, data?: object) =>
  ${entity}Api.partialUpdate(id, data);

/** 删除${模块注释} */
export const delete${Entity} = (id: string) => ${entity}Api.destroy(id);
```

并且更新文件顶部的 import，添加 `import { ${entity}Api } from "./system/${entity}";`

### 3.3 类型定义 — `web/src/views/system/${entity}/utils/types.ts`

模板（参考 `web/src/views/system/dept/utils/types.ts`）：

```typescript
interface FormItemProps {
  id?: string;
  ${higher_options_field}
  ${form_item_fields}
}

interface FormProps {
  formInline: FormItemProps;
}

export type { FormItemProps, FormProps };
```

**规则**：
- 如果树形结构（有 `parent_id`），添加 `higher${Entity}Options: Record<string, unknown>[]` 和 `parentId: string`
- 每个业务字段对应一个表单属性
- `isActive` 类型为 `number`
- 字符串类型默认 `string`，数字类型默认 `number`

### 3.4 校验规则 — `web/src/views/system/${entity}/utils/rule.ts`

模板（参考 `web/src/views/system/dept/utils/rule.ts`）：

```typescript
import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
  name: [{ required: true, message: "${模块注释}名称为必填项", trigger: "blur" }],
  ${extra_rules}
});
```

**规则**：
- 只有 `name` 字段必须有必填校验
- 如果表有 `phone`、`email` 等字段，使用 `@pureadmin/utils` 的 `isPhone`、`isEmail` 做格式校验

### 3.5 Hook — `web/src/views/system/${entity}/utils/hook.tsx`

模板（参考 `web/src/views/system/dept/utils/hook.tsx`）：

```typescript
import dayjs from "dayjs";
import editForm from "../form.vue";
import { message } from "@/utils/message";
import { ${entity}Api } from "@/api/system/${entity}";
import { ElMessageBox } from "element-plus";
import { usePublicHooks } from "../../hooks";
import { addDialog } from "@/components/ReDialog";
import { reactive, ref, onMounted, h } from "vue";
import type { FormItemProps } from "../utils/types";
import { cloneDeep, isAllEmpty, deviceDetection } from "@pureadmin/utils";
${extra_hook_imports}

export function use${Entity}() {
  const form = reactive({
    name: "",
    isActive: null
  });

  const formRef = ref();
  const dataList = ref([]);
  const loading = ref(true);
  const { tagStyle } = usePublicHooks();

  const columns: TableColumnList = [
    ${column_definitions}
    {
      label: "操作",
      fixed: "right",
      width: 210,
      slot: "operation"
    }
  ];

  function handleSelectionChange(val) {
    console.log("handleSelectionChange", val);
  }

  function resetForm(formEl) {
    if (!formEl) return;
    formEl.resetFields();
    onSearch();
  }

  async function onSearch() {
    loading.value = true;
    ${on_search_impl}
    setTimeout(() => {
      loading.value = false;
    }, 500);
  }

  function openDialog(title = "新增", row?: FormItemProps) {
    addDialog({
      title: `${title}${模块注释}`,
      props: {
        formInline: {
          ${higher_options_field}: ${format_higher_options},
          ${dialog_props}
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
                ${payload_fields}
              };

              if (title === "新增") {
                const { code } = await ${entity}Api.create(payload);
                if (code === 0 || code === 201) {
                  message(`成功创建${模块注释} ${curData.name}`, { type: "success" });
                  done();
                  onSearch();
                }
              } else {
                const { code } = await ${entity}Api.partialUpdate(row.id, payload);
                if (code === 0) {
                  message(`成功更新${模块注释} ${curData.name}`, { type: "success" });
                  done();
                  onSearch();
                }
              }
            } catch {
              message(`${title}${模块注释}失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  function handleDelete(row) {
    ElMessageBox.confirm(
      `确认要删除${模块注释} <strong style='color:var(--el-color-primary)'>${row.name}</strong> 吗?`,
      "系统提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
        dangerouslyUseHTMLString: true,
        draggable: true
      }
    )
      .then(async () => {
        const { code } = await ${entity}Api.destroy(row.id);
        if (code === 0) {
          message(`已成功删除${模块注释} ${row.name}`, { type: "success" });
          onSearch();
        }
      })
      .catch(() => {});
  }

  onMounted(() => {
    onSearch();
  });

  return {
    form,
    loading,
    columns,
    dataList,
    onSearch,
    resetForm,
    openDialog,
    handleDelete,
    handleSelectionChange
  };
}
```

**规则**：
- 分页列表使用 `${entity}Api.list(params)` 返回 `ResultTable`
- 树形列表（有 `parent_id`）使用 `handleTree` 和 `formatHigher${Entity}Options`
- 列定义中的日期字段使用 `dayjs().format("YYYY-MM-DD HH:mm:ss")` 格式化
- 状态字段使用 `el-tag` + `tagStyle` 渲染
- 如果树形结构，在 `openDialog` 中使用 `formatHigherDeptOptions(cloneDeep(dataList.value))` 生成级联选择器选项

### 3.6 表单组件 — `web/src/views/system/${entity}/form.vue`

模板（参考 `web/src/views/system/dept/form.vue`）：

```vue
<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { usePublicHooks } from "../../hooks";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    ${form_defaults}
  })
});

const ruleFormRef = ref();
const { switchStyle } = usePublicHooks();
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
    <el-row :gutter="30">
      ${higher_form_item}
      ${form_items}
      <re-col>
        <el-form-item label="描述">
          <el-input
            v-model="newFormInline.description"
            placeholder="请输入描述信息"
            type="textarea"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
```

**规则**：
- 如果树形结构（有 `parent_id`），第一个字段是 `上级xxx`（el-cascader 级联选择器）
- `name` 字段：`el-input`，必填（`prop="name"`）
- `isActive` 字段：`el-switch`（`:active-value="1" :inactive-value="0"`）
- `rank`/排序字段：`el-input-number`（`:min="0" :max="9999"`）
- 其他 varchar 字段：`el-input`
- text 字段：`el-input type="textarea"`
- 使用 `<re-col>` 布局
- 表单字段用 `newFormInline.xxx` 双向绑定

### 3.7 页面组件 — `web/src/views/system/${entity}/index.vue`

模板（参考 `web/src/views/system/dept/index.vue`）：

```vue
<script setup lang="ts">
import { ref } from "vue";
import { use${Entity} } from "./utils/hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "System${Entity}"
});

const formRef = ref();
const tableRef = ref();
const {
  form,
  loading,
  columns,
  dataList,
  onSearch,
  resetForm,
  openDialog,
  handleDelete,
  handleSelectionChange
} = use${Entity}();

function onFullscreen() {
  tableRef.value.setAdaptive();
}
</script>

<template>
  <div class="main">
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
    >
      <el-form-item label="${模块注释}名称：" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入${模块注释}名称"
          clearable
          class="w-45!"
        />
      </el-form-item>
      <el-form-item label="状态：" prop="isActive">
        <el-select
          v-model="form.isActive"
          placeholder="请选择状态"
          clearable
          class="w-45!"
        >
          <el-option label="启用" :value="true" />
          <el-option label="停用" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :icon="useRenderIcon('ri/search-line')"
          :loading="loading"
          @click="onSearch"
        >
          搜索
        </el-button>
        <el-button :icon="useRenderIcon(Refresh)" @click="resetForm(formRef)">
          重置
        </el-button>
      </el-form-item>
    </el-form>

    <PureTableBar
      title="${模块注释}管理"
      :columns="columns"
      :tableRef="tableRef?.getTableRef()"
      @refresh="onSearch"
      @fullscreen="onFullscreen"
    >
      <template #buttons>
        <el-button
          type="primary"
          :icon="useRenderIcon(AddFill)"
          @click="openDialog()"
        >
          新增${模块注释}
        </el-button>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <pure-table
          ref="tableRef"
          adaptive
          :adaptiveConfig="{ offsetBottom: 45 }"
          align-whole="center"
          row-key="id"
          showOverflowTooltip
          table-layout="auto"
          default-expand-all
          :loading="loading"
          :size="size"
          :data="dataList"
          :columns="dynamicColumns"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @selection-change="handleSelectionChange"
        >
          <template #operation="{ row }">
            <el-button
              class="reset-margin"
              link
              type="primary"
              :size="size"
              :icon="useRenderIcon(EditPen)"
              @click="openDialog('修改', row)"
            >
              修改
            </el-button>
            ${add_child_button}
            <el-popconfirm
              :title="`是否确认删除${模块注释}名称为${row.name}的这条数据`"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
                  class="reset-margin"
                  link
                  type="primary"
                  :size="size"
                  :icon="useRenderIcon(Delete)"
                >
                  删除
                </el-button>
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

**规则**：
- 树形表格设置 `default-expand-all` 和 `row-key="id"`
- 分页表格使用 `v-model:pageSize` 和 `v-model:currentPage`
- 组件名称为 `System${Entity}`（PascalCase）
- 操作列包含编辑和删除按钮

### 3.8 前端生成顺序总表

```
1  →  web/src/api/system/{entity}.ts
2  →  web/src/api/system.ts (更新，添加 import 和导出函数)
3  →  web/src/views/system/{entity}/utils/types.ts
4  →  web/src/views/system/{entity}/utils/rule.ts
5  →  web/src/views/system/{entity}/utils/hook.tsx
6  →  web/src/views/system/{entity}/form.vue
7  →  web/src/views/system/{entity}/index.vue
```

---

## 常见表结构的特殊处理

### 树形结构（有 parent_id）
- 后端：实体添加 `parent_id` 字段，仓储添加 `get_by_parent_id` 方法，服务添加 `get_tree` 和 `_build_tree` 方法
- 前端：列表用树形表格（`default-expand-all`），表单用级联选择器（`el-cascader`），操作列添加"新增子节点"按钮，hook 中用 `handleTree()` 和 `formatHigherDeptOptions()`

### 分页列表（无 parent_id）
- 后端：服务返回 `list_response`（分页包装），路由接收 `pageNum`/`pageSize`
- 前端：API 类使用基类 `list`（返回 `ResultTable`），hook 中用分页参数，页面用分页表格

### 有 code 唯一字段
- 后端：仓储添加 `get_by_code`，服务在 `create` 中检查 code 唯一性
- 前端：表单添加 code 输入框

---

## 验证

生成完毕后运行：

后端：
```bash
cd service && ruff check src/ && ruff format src/ && mypy src/
```

前端：
```bash
cd web && pnpm lint && pnpm typecheck
```
