# 后端代码模式参考

本文档包含多种后端框架的代码生成模板。适配新项目时，根据 `project-config.md` 中指定的框架类型选择对应的模式。

---

## 1. FastAPI + DDD 模式

### 1.1 领域实体（domain/entities/{table}.py）

```python
from uuid import UUID
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class {EntityName}(SQLModel, table=False):
    """{模型中文名}"""
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="{字段注释}")
    # ... 其他字段
```

### 1.2 仓储接口（domain/repositories/{table}_repository.py）

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from src.domain.entities.{table} import {EntityName}


class {EntityName}Repository(ABC):
    """{模型名}仓储接口"""
    
    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[{EntityName}]: ...
    
    @abstractmethod
    async def get_all(self) -> List[{EntityName}]: ...
    
    @abstractmethod
    async def create(self, entity: {EntityName}) -> {EntityName}: ...
    
    @abstractmethod
    async def update(self, id: UUID, entity: {EntityName}) -> Optional[{EntityName}]: ...
    
    @abstractmethod
    async def delete(self, id: UUID) -> bool: ...
```

### 1.3 ORM 模型（infrastructure/database/models/{table}.py）

```python
from uuid import UUID
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .user import UserModel


class {ModelName}Model(SQLModel, table=True):
    """{模型中文名}"""
    __tablename__ = "{table_name}"
    
    id: Optional[UUID] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, description="{字段注释}")
    created_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    # ... 其他字段
    
    # 关联字段示例
    # creator_id: Optional[UUID] = Field(foreign_key="user.id")
    # creator: Optional["UserModel"] = Relationship(back_populates="{table}_creator")
```

### 1.4 仓储实现（infrastructure/repositories/{table}_repository.py）

```python
from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.infrastructure.database.models.{table} import {ModelName}Model
from src.domain.entities.{table} import {EntityName}
from src.domain.repositories.{table}_repository import {EntityName}Repository
from src.infrastructure.repositories import BaseRepository


class {EntityName}RepositoryImpl(BaseRepository, {EntityName}Repository):
    """{模型名}仓储实现"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, {ModelName}Model)
    
    def _to_entity(self, model: {ModelName}Model) -> {EntityName}:
        return {EntityName}(
            id=model.id,
            name=model.name,
            # ...
        )
    
    def _to_model(self, entity: {EntityName}) -> {ModelName}Model:
        return {ModelName}Model(
            id=entity.id,
            name=entity.name,
            # ...
        )
```

### 1.5 DTO（application/dto/{table}_dto.py）

```python
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime


class {EntityName}CreateDTO(BaseModel):
    """创建 {模型名} DTO"""
    name: str = Field(..., max_length=100, description="{字段注释}")


class {EntityName}UpdateDTO(BaseModel):
    """更新 {模型名} DTO"""
    name: Optional[str] = Field(None, max_length=100, description="{字段注释}")


class {EntityName}ResponseDTO(BaseModel):
    """{模型名} 响应 DTO"""
    id: Optional[UUID] = None
    name: str
    created_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True
```

### 1.6 应用服务（application/services/{table}_service.py）

```python
from typing import List, Optional
from uuid import UUID
from src.domain.repositories.{table}_repository import {EntityName}Repository
from src.application.dto.{table}_dto import (
    {EntityName}CreateDTO,
    {EntityName}UpdateDTO,
    {EntityName}ResponseDTO,
)


class {EntityName}Service:
    """{模型名}应用服务"""
    
    def __init__(self, repository: {EntityName}Repository):
        self.repository = repository
    
    async def get_by_id(self, id: UUID) -> Optional[{EntityName}ResponseDTO]:
        entity = await self.repository.get_by_id(id)
        if entity:
            return {EntityName}ResponseDTO.model_validate(entity)
        return None
    
    async def get_all(self) -> List[{EntityName}ResponseDTO]:
        entities = await self.repository.get_all()
        return [{EntityName}ResponseDTO.model_validate(e) for e in entities]
    
    async def create(self, dto: {EntityName}CreateDTO) -> {EntityName}ResponseDTO:
        entity = {EntityName}(name=dto.name, ...)
        created = await self.repository.create(entity)
        return {EntityName}ResponseDTO.model_validate(created)
    
    async def update(self, id: UUID, dto: {EntityName}UpdateDTO) -> Optional[{EntityName}ResponseDTO]:
        existing = await self.repository.get_by_id(id)
        if not existing:
            return None
        # 更新字段
        for key, value in dto.model_dump(exclude_unset=True).items():
            setattr(existing, key, value)
        updated = await self.repository.update(id, existing)
        return {EntityName}ResponseDTO.model_validate(updated) if updated else None
    
    async def delete(self, id: UUID) -> bool:
        return await self.repository.delete(id)
```

### 1.7 API 路由（api/v1/{table}_router.py）

```python
from classy_fastapi import Routable, get, post, put, delete
from fastapi import Depends
from typing import List
from uuid import UUID

from src.api.dependencies import get_{table}_repository
from src.api.common import success_response, list_response
from src.application.dto.{table}_dto import (
    {EntityName}CreateDTO,
    {EntityName}UpdateDTO,
)
from src.domain.repositories.{table}_repository import {EntityName}Repository
from src.application.services.{table}_service import {EntityName}Service


class {EntityName}Router(Routable):
    """{模型名}管理路由"""
    
    def __init__(self):
        super().__init__(prefix="/{table}", tags=["{模型名}"])
    
    @get("")
    async def get_list(
        self,
        service: {EntityName}Service = Depends(self._get_service),
    ) -> dict:
        items = await service.get_all()
        return list_response([item.model_dump() for item in items], total=len(items))
    
    @get("/{item_id}")
    async def get_detail(
        self,
        item_id: UUID,
        service: {EntityName}Service = Depends(self._get_service),
    ) -> dict:
        item = await service.get_by_id(item_id)
        return success_response(data=item.model_dump() if item else None)
    
    @post("")
    async def create(
        self,
        dto: {EntityName}CreateDTO,
        service: {EntityName}Service = Depends(self._get_service),
    ) -> dict:
        item = await service.create(dto)
        return success_response(data=item.model_dump(), message="创建成功", code=201)
    
    @put("/{item_id}")
    async def update(
        self,
        item_id: UUID,
        dto: {EntityName}UpdateDTO,
        service: {EntityName}Service = Depends(self._get_service),
    ) -> dict:
        item = await service.update(item_id, dto)
        return success_response(data=item.model_dump() if item else None, message="更新成功")
    
    @delete("/{item_id}")
    async def delete(
        self,
        item_id: UUID,
        service: {EntityName}Service = Depends(self._get_service),
    ) -> dict:
        success = await service.delete(item_id)
        return success_response(message="删除成功" if success else "删除失败")
    
    def _get_service(self, repository: {EntityName}Repository = Depends(get_{table}_repository)) -> {EntityName}Service:
        return {EntityName}Service(repository)
```

---

## 2. Django REST Framework 模式

> 详情参考原 xadmin-crud 技能的 backend-patterns.md

### 2.1 Model 模式

```python
from django.db import models
from common.core.models import DbAuditModel


class {ModelName}(DbAuditModel):
    """{模型中文名}"""
    
    name = models.CharField(max_length=100, verbose_name="{字段注释}")
    
    class Meta:
        verbose_name = '{模型中文名}'
        verbose_name_plural = verbose_name
    
    def __str__(self):
        return self.name
```

### 2.2 Serializer 模式

```python
from rest_framework import serializers
from common.core.serializers import BaseModelSerializer
from {app} import models


class {ModelName}Serializer(BaseModelSerializer):
    class Meta:
        model = models.{ModelName}
        fields = ['pk', 'name', ...]
```

### 2.3 ViewSet 模式

```python
from common.core.modelset import BaseModelSet
from common.core.filter import BaseFilterSet
from {app}.models import {ModelName}
from {app}.serializers.{table} import {ModelName}Serializer


class {ModelName}Filter(BaseFilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    
    class Meta:
        model = {ModelName}
        fields = ['name']


class {ModelName}ViewSet(BaseModelSet):
    """{模型中文名}"""
    queryset = {ModelName}.objects.all()
    serializer_class = {ModelName}Serializer
    filterset_class = {ModelName}Filter
```

### 2.4 URL 模式

```python
from rest_framework.routers import SimpleRouter
from {app}.views.{table} import {ModelName}ViewSet

router = SimpleRouter(False)
router.register('{route}', {ModelName}ViewSet, basename='{route}')
urlpatterns = router.urls
```