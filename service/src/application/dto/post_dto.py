"""应用层 - 岗位领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none


class PostCreateDTO(BaseModel):
    """创建岗位请求"""

    postCode: str = Field(min_length=1, max_length=64, description="岗位编码(唯一)")
    postName: str = Field(min_length=1, max_length=64, description="岗位名称")
    postSort: int = Field(default=0, ge=0, description="显示排序")
    isActive: int = Field(default=1, ge=0, le=1, description="状态（1正常 0停用）")
    remark: str | None = Field(default=None, max_length=256, description="备注")

    @field_validator("remark", mode="before")
    @classmethod
    def validate_remark(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class PostUpdateDTO(BaseModel):
    """更新岗位请求"""

    postCode: str | None = Field(default=None, min_length=1, max_length=64, description="岗位编码(唯一)")
    postName: str | None = Field(default=None, min_length=1, max_length=64, description="岗位名称")
    postSort: int | None = Field(default=None, ge=0, description="显示排序")
    isActive: int | None = Field(default=None, ge=0, le=1, description="状态（1正常 0停用）")
    remark: str | None = Field(default=None, max_length=256, description="备注")

    @field_validator("remark", mode="before")
    @classmethod
    def validate_remark(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class PostResponseDTO(BaseModel):
    """岗位响应"""

    id: str
    postCode: str
    postName: str
    postSort: int = 0
    isActive: int = 1
    remark: str = ""
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None

    model_config = {"from_attributes": True}


class PostListQueryDTO(BaseModel):
    """岗位列表查询"""

    pageNum: int = Field(default=1, ge=1)
    pageSize: int = Field(default=10, ge=1, le=100)
    postCode: str | None = None
    postName: str | None = None
    isActive: int | None = None

    @field_validator("postCode", "postName", mode="before")
    @classmethod
    def validate_empty(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)
