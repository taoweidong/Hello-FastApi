"""应用层 - 菜单领域的数据传输对象。"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from src.application.validators import empty_str_to_none, normalize_optional_id


class MenuMetaDTO(BaseModel):
    """菜单元数据响应（嵌套在 MenuResponseDTO 中）"""

    id: str
    title: str | None = None
    icon: str | None = None
    rSvgName: str | None = None
    isShowMenu: int = 1
    isShowParent: int = 0
    isKeepalive: int = 0
    frameUrl: str | None = None
    frameLoading: int = 1
    transitionEnter: str | None = None
    transitionLeave: str | None = None
    isHiddenTag: int = 0
    fixedTag: int = 0
    dynamicLevel: int = 0

    model_config = {"from_attributes": True}


class MenuCreateDTO(BaseModel):
    """创建菜单请求"""

    parentId: str | int | None = None  # 父菜单ID，None、空字符串或0表示顶级菜单

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v) -> str | None:
        """将 parentId 统一处理：int 0、空字符串、None 都转换为 None 表示顶级菜单。"""
        return normalize_optional_id(v)

    menuType: int = Field(default=0, description="菜单类型(0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限)")
    name: str = Field(max_length=128, description="菜单名称(唯一)")
    path: str | None = Field(default=None, max_length=255, description="路由路径")
    component: str | None = Field(default=None, max_length=255, description="组件路径")
    rank: int = Field(default=0, description="排序号")
    isActive: int = Field(default=1, description="是否启用")
    method: str | None = Field(default=None, max_length=10, description="HTTP方法，用于PERMISSION类型")
    description: str | None = Field(default=None, max_length=256)

    # 菜单元数据字段（创建时一起提交）
    title: str | None = Field(default=None, max_length=255, description="菜单显示标题")
    icon: str | None = Field(default=None, max_length=255, description="菜单图标")
    rSvgName: str | None = Field(default=None, max_length=255, description="SVG图标名称")
    isShowMenu: int = Field(default=1, description="是否在菜单中显示")
    isShowParent: int = Field(default=0, description="是否显示父级菜单")
    isKeepalive: int = Field(default=0, description="是否缓存页面")
    frameUrl: str | None = Field(default=None, max_length=255, description="iframe内嵌链接")
    frameLoading: int = Field(default=1, description="iframe加载动画")
    transitionEnter: str | None = Field(default=None, max_length=255, description="进场动画名称")
    transitionLeave: str | None = Field(default=None, max_length=255, description="离场动画名称")
    isHiddenTag: int = Field(default=0, description="禁止添加到标签页")
    fixedTag: int = Field(default=0, description="固定标签页")
    dynamicLevel: int = Field(default=0, description="动态路由层级")

    @field_validator("name", "path", "component", "method", "description", "title", "icon", "rSvgName", "frameUrl", "transitionEnter", "transitionLeave", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class MenuUpdateDTO(BaseModel):
    """更新菜单请求"""

    parentId: str | int | None = None  # 父菜单ID，None、空字符串或0表示顶级菜单

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | int | None) -> str | None:
        """将 parentId 统一处理：int 0、空字符串、None 都转换为 None 表示顶级菜单。"""
        return normalize_optional_id(v)

    menuType: int | None = Field(default=None, description="菜单类型(0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限)")
    name: str | None = Field(default=None, max_length=128, description="菜单名称(唯一)")
    path: str | None = Field(default=None, max_length=255, description="路由路径")
    component: str | None = Field(default=None, max_length=255, description="组件路径")
    rank: int | None = None
    isActive: int | None = Field(default=None, description="是否启用")
    method: str | None = Field(default=None, max_length=10, description="HTTP方法，用于PERMISSION类型")
    description: str | None = Field(default=None, max_length=256)

    # 菜单元数据字段
    title: str | None = Field(default=None, max_length=255, description="菜单显示标题")
    icon: str | None = Field(default=None, max_length=255, description="菜单图标")
    rSvgName: str | None = Field(default=None, max_length=255, description="SVG图标名称")
    isShowMenu: int | None = Field(default=None, description="是否在菜单中显示")
    isShowParent: int | None = Field(default=None, description="是否显示父级菜单")
    isKeepalive: int | None = Field(default=None, description="是否缓存页面")
    frameUrl: str | None = Field(default=None, max_length=255, description="iframe内嵌链接")
    frameLoading: int | None = Field(default=None, description="iframe加载动画")
    transitionEnter: str | None = Field(default=None, max_length=255, description="进场动画名称")
    transitionLeave: str | None = Field(default=None, max_length=255, description="离场动画名称")
    isHiddenTag: int | None = Field(default=None, description="禁止添加到标签页")
    fixedTag: int | None = Field(default=None, description="固定标签页")
    dynamicLevel: int | None = Field(default=None, description="动态路由层级")

    @field_validator("name", "path", "component", "method", "description", "title", "icon", "rSvgName", "frameUrl", "transitionEnter", "transitionLeave", mode="before")
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class MenuResponseDTO(BaseModel):
    """菜单响应"""

    id: str
    parentId: str | None = None
    menuType: int = 0
    name: str = ""
    path: str = ""
    component: str | None = None
    rank: int = 0
    isActive: int = 1
    method: str | None = None
    metaId: str = ""
    meta: MenuMetaDTO | None = None
    creatorId: str | None = None
    modifierId: str | None = None
    createdTime: datetime | None = None
    updatedTime: datetime | None = None
    description: str | None = None
    children: list["MenuResponseDTO"] = []

    model_config = {"from_attributes": True}


# 解决前向引用
MenuResponseDTO.model_rebuild()
