"""应用层 - 菜单领域的数据传输对象。"""


from pydantic import BaseModel, Field, field_validator

from src.core.validators import empty_str_to_none


class MenuCreateDTO(BaseModel):
    """创建菜单请求"""
    parentId: str | int | None = None  # 父菜单ID，None、空字符串或0表示顶级菜单

    @field_validator('parentId', mode='before')
    @classmethod
    def validate_parent_id(cls, v) -> str | None:
        """将 parentId 统一处理：int 0、空字符串、None 都转换为 None 表示顶级菜单。"""
        if v is None or v == '' or v == 0 or v == '0':
            return None
        if isinstance(v, int):
            return str(v)
        return v
    menuType: int = 0  # 菜单类型(0-菜单, 1-iframe, 2-外链, 3-按钮)
    title: str = Field(max_length=64)  # 菜单名称
    name: str | None = Field(default=None, max_length=64)  # 路由name
    path: str | None = Field(default=None, max_length=256)  # 路由路径
    component: str | None = Field(default=None, max_length=256)  # 组件路径
    rank: int = 99  # 排序号
    redirect: str | None = Field(default=None, max_length=256)  # 重定向路径
    icon: str | None = Field(default=None, max_length=64)  # 图标
    extraIcon: str | None = Field(default=None, max_length=64)  # 菜单名称右侧额外图标
    enterTransition: str | None = Field(default=None, max_length=64)  # 进场动画
    leaveTransition: str | None = Field(default=None, max_length=64)  # 离场动画
    activePath: str | None = Field(default=None, max_length=256)  # 激活菜单路径
    auths: str | None = Field(default=None, max_length=500)  # 权限标识
    frameSrc: str | None = Field(default=None, max_length=500)  # iframe链接地址
    frameLoading: bool = True  # iframe首次加载动画
    keepAlive: bool = False  # 是否缓存页面
    hiddenTag: bool = False  # 禁止添加到标签页
    fixedTag: bool = False  # 固定标签页
    showLink: bool = True  # 是否显示菜单
    showParent: bool = False  # 是否显示父级菜单

    @field_validator('title', 'name', 'path', 'component', 'redirect',
                     'icon', 'extraIcon', 'enterTransition', 'leaveTransition',
                     'activePath', 'auths', 'frameSrc', mode='before')
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class MenuUpdateDTO(BaseModel):
    """更新菜单请求"""
    parentId: str | int | None = None  # 父菜单ID，None、空字符串或0表示顶级菜单

    @field_validator('parentId', mode='before')
    @classmethod
    def validate_parent_id(cls, v) -> str | None:
        """将 parentId 统一处理：int 0、空字符串、None 都转换为 None 表示顶级菜单。"""
        if v is None or v == '' or v == 0 or v == '0':
            return None
        if isinstance(v, int):
            return str(v)
        return v
    menuType: int | None = None  # 菜单类型(0-菜单, 1-iframe, 2-外链, 3-按钮)
    title: str | None = Field(default=None, max_length=64)  # 菜单名称
    name: str | None = Field(default=None, max_length=64)  # 路由name
    path: str | None = Field(default=None, max_length=256)  # 路由路径
    component: str | None = Field(default=None, max_length=256)  # 组件路径
    rank: int | None = None  # 排序号
    redirect: str | None = Field(default=None, max_length=256)  # 重定向路径
    icon: str | None = Field(default=None, max_length=64)  # 图标
    extraIcon: str | None = Field(default=None, max_length=64)  # 菜单名称右侧额外图标
    enterTransition: str | None = Field(default=None, max_length=64)  # 进场动画
    leaveTransition: str | None = Field(default=None, max_length=64)  # 离场动画
    activePath: str | None = Field(default=None, max_length=256)  # 激活菜单路径
    auths: str | None = Field(default=None, max_length=500)  # 权限标识
    frameSrc: str | None = Field(default=None, max_length=500)  # iframe链接地址
    frameLoading: bool | None = None  # iframe首次加载动画
    keepAlive: bool | None = None  # 是否缓存页面
    hiddenTag: bool | None = None  # 禁止添加到标签页
    fixedTag: bool | None = None  # 固定标签页
    showLink: bool | None = None  # 是否显示菜单
    showParent: bool | None = None  # 是否显示父级菜单
    status: int | None = None  # 状态(0-禁用, 1-启用)

    @field_validator('title', 'name', 'path', 'component', 'redirect',
                     'icon', 'extraIcon', 'enterTransition', 'leaveTransition',
                     'activePath', 'auths', 'frameSrc', mode='before')
    @classmethod
    def validate_empty_str(cls, v: str | None) -> str | None:
        """将空字符串转换为 None。"""
        return empty_str_to_none(v)


class MenuResponseDTO(BaseModel):
    """菜单响应"""
    id: str  # 菜单ID (UUID格式)
    parentId: str | int = 0  # 父菜单ID，0表示顶级菜单
    menuType: int = 0  # 菜单类型(0-菜单, 1-iframe, 2-外链, 3-按钮)
    title: str  # 菜单名称
    name: str | None = None  # 路由name
    path: str | None = None  # 路由路径
    component: str | None = None  # 组件路径
    rank: int = 99  # 排序号
    redirect: str | None = None  # 重定向路径
    icon: str | None = None  # 图标
    extraIcon: str | None = None  # 菜单名称右侧额外图标
    enterTransition: str | None = None  # 进场动画
    leaveTransition: str | None = None  # 离场动画
    activePath: str | None = None  # 激活菜单路径
    auths: str | None = None  # 权限标识
    frameSrc: str | None = None  # iframe链接地址
    frameLoading: bool = True  # iframe首次加载动画
    keepAlive: bool = False  # 是否缓存页面
    hiddenTag: bool = False  # 禁止添加到标签页
    fixedTag: bool = False  # 固定标签页
    showLink: bool = True  # 是否显示菜单
    showParent: bool = False  # 是否显示父级菜单
    status: int = 1  # 状态(0-禁用, 1-启用)
    children: list["MenuResponseDTO"] = []  # 子菜单列表
    createTime: str | None = None  # 创建时间
    updateTime: str | None = None  # 更新时间

    model_config = {"from_attributes": True}


# 解决前向引用
MenuResponseDTO.model_rebuild()
