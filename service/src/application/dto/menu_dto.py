"""应用层 - 菜单领域的数据传输对象。"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.application.validators import empty_str_to_none, normalize_optional_id


class MenuMetaFlattenMixin:
    """把嵌套 `meta` 载荷提升为顶层扁平字段的 Mixin。

    菜单接口的读写契约都是「嵌套 meta」：响应 DTO 是 `MenuResponseDTO.meta`
    （MenuMetaDTO），前端表单提交 `meta: {title, icon, ...}`，后端集成测试
    同样提交嵌套 meta。但创建/更新 DTO 早期只声明了扁平字段，而 pydantic
    默认忽略额外字段（extra="ignore"）→ 嵌套 meta 被**静默丢弃**，
    `title` 回落为 `name`（表现为：页面里填的「菜单名称」不生效，
    菜单标题变成路由名称）。

    这里在 `mode="before"` 阶段做提升，规则：
    - 嵌套 `meta.<字段>` 优先，写回同名扁平字段；
    - 扁平字段保留，作为向后兼容的备选（新旧两种载荷都收）；
    - `None` 值不覆盖，与 `update_info` 的「None 表示不更新」语义一致。
    """

    @model_validator(mode="before")
    @classmethod
    def flatten_meta(cls, values):
        if not isinstance(values, dict):
            return values
        meta = values.get("meta")
        if not isinstance(meta, dict):
            return values
        merged = {k: v for k, v in values.items() if k != "meta"}
        fields = cls.model_fields
        for key, val in meta.items():
            if key != "meta" and key in fields and val is not None:
                merged[key] = val
        return merged


class MenuStringValidator:
    """菜单字符串字段验证器 Mixin"""

    @field_validator(
        "name",
        "path",
        "component",
        "method",
        "description",
        "title",
        "icon",
        "rSvgName",
        "frameUrl",
        "transitionEnter",
        "transitionLeave",
        mode="before",
    )
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        return empty_str_to_none(v)


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


class MenuCreateDTO(MenuMetaFlattenMixin, BaseModel, MenuStringValidator):
    """创建菜单请求"""

    parentId: str | int | None = None

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v) -> str | None:
        return normalize_optional_id(v)

    menuType: int = Field(default=0, description="菜单类型(0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限)")
    name: str = Field(max_length=128, description="菜单名称(唯一)")
    path: str | None = Field(default=None, max_length=255, description="路由路径")
    component: str | None = Field(default=None, max_length=255, description="组件路径")
    rank: int = Field(default=0, description="排序号")
    isActive: int = Field(default=1, description="是否启用")
    method: str | None = Field(default=None, max_length=10, description="HTTP方法，用于PERMISSION类型")
    description: str | None = Field(default=None, max_length=256)
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

    # 嵌套 meta 载荷：菜单接口的读写契约都是嵌套 meta（响应为 MenuResponseDTO.meta）。
    # 声明该字段是为类型标注与接口文档；其值由 MenuMetaFlattenMixin 提升到上方同名
    # 扁平字段，服务层仍然只读扁平字段。
    meta: dict[str, Any] | None = Field(default=None, description="菜单元数据（嵌套载荷，字段提升到顶层同名扁平字段）")


class MenuUpdateDTO(MenuMetaFlattenMixin, BaseModel, MenuStringValidator):
    """更新菜单请求"""

    parentId: str | int | None = None

    @field_validator("parentId", mode="before")
    @classmethod
    def validate_parent_id(cls, v: str | int | None) -> str | None:
        return normalize_optional_id(v)

    menuType: int | None = Field(default=None, description="菜单类型(0-DIRECTORY目录, 1-MENU页面, 2-PERMISSION权限)")
    name: str | None = Field(default=None, max_length=128, description="菜单名称(唯一)")
    path: str | None = Field(default=None, max_length=255, description="路由路径")
    component: str | None = Field(default=None, max_length=255, description="组件路径")
    rank: int | None = None
    isActive: int | None = Field(default=None, description="是否启用")
    method: str | None = Field(default=None, max_length=10, description="HTTP方法，用于PERMISSION类型")
    description: str | None = Field(default=None, max_length=256)
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

    # 同 MenuCreateDTO.meta：声明以便类型标注与接口文档，值由 mixin 提升到扁平字段
    meta: dict[str, Any] | None = Field(default=None, description="菜单元数据（嵌套载荷，字段提升到顶层同名扁平字段）")


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


MenuResponseDTO.model_rebuild()
