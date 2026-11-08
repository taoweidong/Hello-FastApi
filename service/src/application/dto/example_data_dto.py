"""应用层 - 示例数据领域的数据传输对象（Univer 表格 CRUD 示例）。"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from src.application.dto.common import BaseListQueryDTO
from src.application.validators import empty_str_to_none


class ExampleDataCreateDTO(BaseModel):
    """创建示例数据"""

    name: str = Field(min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    quantity: int = Field(default=0, ge=0)
    price: float = Field(default=0.0, ge=0)
    recordDate: date | None = None
    note: str | None = Field(default=None, max_length=512)

    @field_validator("category", "note", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)

    @field_validator("quantity", "price", mode="before")
    @classmethod
    def _empty_to_zero(cls, v):
        """电子表格单元格空串按 0 处理。"""
        if v == "" or v is None:
            return 0
        return v


class ExampleDataUpdateDTO(BaseModel):
    """更新示例数据（Univer 全行回写语义：字段齐全）"""

    name: str = Field(min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    quantity: int = Field(default=0, ge=0)
    price: float = Field(default=0.0, ge=0)
    recordDate: date | None = None
    note: str | None = Field(default=None, max_length=512)
    isActive: int = Field(default=1, ge=0, le=1)

    @field_validator("category", "note", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)

    @field_validator("quantity", "price", mode="before")
    @classmethod
    def _empty_to_zero(cls, v):
        if v == "" or v is None:
            return 0
        return v


class ExampleDataResponseDTO(BaseModel):
    """示例数据响应"""

    id: str
    name: str
    category: str | None = None
    quantity: int = 0
    price: float = 0.0
    recordDate: date | None = None
    note: str | None = None
    isActive: int = 1
    creatorId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None

    model_config = {"from_attributes": True}


class ExampleDataListQueryDTO(BaseListQueryDTO):
    """示例数据列表查询"""

    name: str | None = None
    category: str | None = None
    isActive: int | None = None

    @field_validator("name", "category", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)


class ExampleDataBatchItem(BaseModel):
    """批量保存条目（Univer 页面回写）。

    电子表格空单元格的语义：category/note/recordDate 空 → None；
    quantity/price 空 → 0。
    """

    id: str | None = Field(default=None, description="有 id 视为更新，无 id 视为新增")
    name: str = Field(min_length=1, max_length=128)
    category: str | None = Field(default=None, max_length=64)
    quantity: int = Field(default=0, ge=0)
    price: float = Field(default=0.0, ge=0)
    recordDate: date | None = None
    note: str | None = Field(default=None, max_length=512)
    isActive: int = Field(default=1, ge=0, le=1)

    @field_validator("category", "note", mode="before")
    @classmethod
    def _empty_to_none(cls, v):
        return empty_str_to_none(v)

    @field_validator("quantity", "price", mode="before")
    @classmethod
    def _empty_to_zero(cls, v):
        if v == "" or v is None:
            return 0
        return v


class ExampleDataBatchSaveDTO(BaseModel):
    """批量保存：creates + updates + deletes（Univer 差异回写契约）"""

    creates: list[ExampleDataBatchItem] = Field(default_factory=list, max_length=1000)
    updates: list[ExampleDataBatchItem] = Field(default_factory=list, max_length=1000)
    deletes: list[str] = Field(default_factory=list, max_length=1000)
