"""应用层 - 字典领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none, normalize_optional_id


class DictionaryCreateDTO(BaseModel):
    """创建字典请求"""

    name: str = Field(max_length=64, description="字典名称")
    label: str = Field(default="", max_length=128, description="显示标签")
    value: str = Field(default="", max_length=128, description="字典值")
    parentId: str | None = Field(default=None, description="父字典ID，None表示顶级字典")
    sort: int | None = Field(default=None, description="排序号，未指定则自动递增")
    isActive: int = Field(default=1, description="是否启用")
    description: str | None = Field(default=None, max_length=500)

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | None) -> str | None:
        """将 parentId 统一处理：空字符串、0、'0'、None 转换为 None。"""
        return normalize_optional_id(v)

    @field_validator("description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("sort", mode="before")
    @classmethod
    def validate_sort(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None（表示自动递增）。"""
        if v == "" or v == 0 or v is None:
            return None
        return int(v) if isinstance(v, str) else v

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_is_active(cls, v: int | str | None) -> int:
        """将空字符串或 None 转换为 1。"""
        if v == "" or v is None:
            return 1
        return int(v) if isinstance(v, str) else v


class DictionaryUpdateDTO(BaseModel):
    """更新字典请求"""

    name: str | None = Field(default=None, max_length=64, description="字典名称")
    label: str | None = Field(default=None, max_length=128, description="显示标签")
    value: str | None = Field(default=None, max_length=128, description="字典值")
    parentId: str | None = Field(default=None, description="父字典ID")
    sort: int | None = None
    isActive: int | None = None
    description: str | None = Field(default=None, max_length=500)

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | None) -> str | None:
        """将 parentId 统一处理：空字符串、0、'0'、None 转换为 None。"""
        return normalize_optional_id(v)

    @field_validator("name", "label", "value", "description", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)

    @field_validator("sort", mode="before")
    @classmethod
    def validate_sort(cls, v: int | str | None) -> int | None:
        """将空字符串或 0 转换为 None。"""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        if v == 0:
            return None
        return v

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_is_active(cls, v: int | str | None) -> int | None:
        """将空字符串转换为 None，保留 0 值。"""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v


class DictionaryResponseDTO(BaseModel):
    """字典响应"""

    id: str
    parentId: str | None
    name: str
    label: str = ""
    value: str = ""
    sort: int = 0
    isActive: int = 1
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class DictionaryListQueryDTO(BaseModel):
    """字典列表查询请求"""

    name: str | None = None
    isActive: int | None = None

    @field_validator("isActive", mode="before")
    @classmethod
    def validate_status(cls, v):
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)
