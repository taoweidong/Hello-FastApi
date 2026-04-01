"""数据库模型定义。

此模块使用 SQLModel 定义所有 ORM 模型。
SQLModel 同时充当 SQLAlchemy ORM 模型和 Pydantic 数据模型，
减少了重复的模型定义代码。
"""

# 注意：不要使用 from __future__ import annotations，
# 否则会导致 SQLModel Relationship 类型解析问题

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.domain.entities.department import DepartmentEntity
    from src.domain.entities.log import LoginLogEntity, OperationLogEntity, SystemLogEntity
    from src.domain.entities.menu import MenuEntity
    from src.domain.entities.permission import PermissionEntity
    from src.domain.entities.role import RoleEntity
    from src.domain.entities.user import UserEntity

# ============ 关联模型 ============


class RolePermissionLink(SQLModel, table=True):
    """角色-权限关联表（用于多对多关系）。"""

    __tablename__ = "sys_role_permissions"

    role_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True))
    permission_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_permissions.id", ondelete="CASCADE"), primary_key=True))


# ============ 用户模型 ============


class User(SQLModel, table=True):
    """用户实体。"""

    __tablename__ = "sys_users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50, unique=True, index=True)
    email: str | None = Field(default=None, max_length=100, sa_column_kwargs={"unique": True, "nullable": True}, index=True)
    hashed_password: str = Field(max_length=255)
    nickname: str | None = Field(default=None, max_length=64)  # 昵称
    avatar: str | None = Field(default=None, max_length=500)  # 头像URL
    phone: str | None = Field(default=None, max_length=20)  # 手机号
    sex: int | None = Field(default=None)  # 性别(0-男, 1-女)
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    dept_id: str | None = Field(default=None)  # 部门ID
    remark: str | None = Field(default=None, max_length=500)  # 备注
    is_superuser: bool = Field(default=False)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    # 关系
    roles: List["UserRole"] = Relationship(back_populates="user", sa_relationship_kwargs={"lazy": "selectin"})

    @property
    def is_active(self) -> bool:
        """是否启用（兼容属性，status=1表示启用）。"""
        return self.status == 1

    def to_domain(self) -> "UserEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.user import UserEntity

        return UserEntity(
            id=self.id,
            username=self.username,
            hashed_password=self.hashed_password,
            email=self.email,
            nickname=self.nickname,
            avatar=self.avatar,
            phone=self.phone,
            sex=self.sex,
            status=self.status,
            dept_id=self.dept_id,
            remark=self.remark,
            is_superuser=self.is_superuser,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "UserEntity") -> "User":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            username=entity.username,
            hashed_password=entity.hashed_password,
            email=entity.email,
            nickname=entity.nickname,
            avatar=entity.avatar,
            phone=entity.phone,
            sex=entity.sex,
            status=entity.status,
            dept_id=entity.dept_id,
            remark=entity.remark,
            is_superuser=entity.is_superuser,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


# ============ RBAC 模型 ============


class Role(SQLModel, table=True):
    """角色实体。"""

    __tablename__ = "sys_roles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=50, unique=True, index=True)
    code: str = Field(max_length=64, sa_column_kwargs={"unique": True})  # 角色编码，唯一
    description: str | None = Field(default=None, max_length=255)
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    # 关系
    permissions: List["Permission"] = Relationship(back_populates="roles", link_model=RolePermissionLink, sa_relationship_kwargs={"lazy": "selectin"})
    users: List["UserRole"] = Relationship(back_populates="role", sa_relationship_kwargs={"lazy": "selectin"})

    def to_domain(self) -> "RoleEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.role import RoleEntity

        return RoleEntity(id=self.id, name=self.name, code=self.code, description=self.description, status=self.status, created_at=self.created_at, updated_at=self.updated_at)

    @classmethod
    def from_domain(cls, entity: "RoleEntity") -> "Role":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, code=entity.code, description=entity.description, status=entity.status, created_at=entity.created_at, updated_at=entity.updated_at)

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(SQLModel, table=True):
    """权限实体。"""

    __tablename__ = "sys_permissions"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=100)
    code: str = Field(max_length=100, unique=True, index=True)  # 权限编码（原codename）
    category: str | None = Field(default=None, max_length=64)  # 权限分类
    description: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    resource: str | None = Field(default=None, max_length=50)
    action: str | None = Field(default=None, max_length=20)
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    # 关系
    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink, sa_relationship_kwargs={"lazy": "selectin"})

    def to_domain(self) -> "PermissionEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.permission import PermissionEntity

        return PermissionEntity(id=self.id, name=self.name, code=self.code, category=self.category, description=self.description, resource=self.resource, action=self.action, status=self.status, created_at=self.created_at)

    @classmethod
    def from_domain(cls, entity: "PermissionEntity") -> "Permission":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, code=entity.code, category=entity.category, description=entity.description, resource=entity.resource, action=entity.action, status=entity.status, created_at=entity.created_at)

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, code={self.code})>"


class UserRole(SQLModel, table=True):
    """用户-角色关联表。"""

    __tablename__ = "sys_user_roles"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    user_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_users.id", ondelete="CASCADE"), nullable=False))
    role_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), nullable=False))
    assigned_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    # 关系
    user: Optional["User"] = Relationship(back_populates="roles")
    role: Optional["Role"] = Relationship(back_populates="users")

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


# ============ 菜单模型 ============


class Menu(SQLModel, table=True):
    """菜单实体模型。"""

    __tablename__ = "sys_menus"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=64)  # 菜单名称
    path: str | None = Field(default=None, max_length=256)  # 路由路径
    component: str | None = Field(default=None, max_length=256)  # 组件路径
    icon: str | None = Field(default=None, max_length=64)  # 图标
    title: str | None = Field(default=None, max_length=64)  # 显示标题
    show_link: int = Field(default=1)  # 是否显示(0-隐藏, 1-显示)
    parent_id: str | None = Field(default=None, foreign_key="sys_menus.id")  # 父菜单ID
    order_num: int = Field(default=0)  # 排序号
    permissions: str | None = Field(default=None, max_length=500)  # 关联权限编码，逗号分隔
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    # Pure Admin 扩展字段
    menu_type: int = Field(default=0)  # 菜单类型(0-菜单, 1-iframe, 2-外链, 3-按钮)
    redirect: str | None = Field(default=None, max_length=256)  # 重定向路径
    extra_icon: str | None = Field(default=None, max_length=64)  # 菜单名称右侧额外图标
    enter_transition: str | None = Field(default=None, max_length=64)  # 进场动画
    leave_transition: str | None = Field(default=None, max_length=64)  # 离场动画
    active_path: str | None = Field(default=None, max_length=256)  # 激活菜单路径
    frame_src: str | None = Field(default=None, max_length=500)  # iframe链接地址
    frame_loading: bool = Field(default=True)  # iframe首次加载动画
    keep_alive: bool = Field(default=False)  # 是否缓存页面
    hidden_tag: bool = Field(default=False)  # 禁止添加到标签页
    fixed_tag: bool = Field(default=False)  # 固定标签页
    show_parent: bool = Field(default=False)  # 是否显示父级菜单
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    def to_domain(self) -> "MenuEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.menu import MenuEntity

        return MenuEntity(
            id=self.id,
            name=self.name,
            path=self.path,
            component=self.component,
            icon=self.icon,
            title=self.title,
            show_link=self.show_link,
            parent_id=self.parent_id,
            order_num=self.order_num,
            permissions=self.permissions,
            status=self.status,
            menu_type=self.menu_type,
            redirect=self.redirect,
            extra_icon=self.extra_icon,
            enter_transition=self.enter_transition,
            leave_transition=self.leave_transition,
            active_path=self.active_path,
            frame_src=self.frame_src,
            frame_loading=self.frame_loading,
            keep_alive=self.keep_alive,
            hidden_tag=self.hidden_tag,
            fixed_tag=self.fixed_tag,
            show_parent=self.show_parent,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, entity: "MenuEntity") -> "Menu":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            name=entity.name,
            path=entity.path,
            component=entity.component,
            icon=entity.icon,
            title=entity.title,
            show_link=entity.show_link,
            parent_id=entity.parent_id,
            order_num=entity.order_num,
            permissions=entity.permissions,
            status=entity.status,
            menu_type=entity.menu_type,
            redirect=entity.redirect,
            extra_icon=entity.extra_icon,
            enter_transition=entity.enter_transition,
            leave_transition=entity.leave_transition,
            active_path=entity.active_path,
            frame_src=entity.frame_src,
            frame_loading=entity.frame_loading,
            keep_alive=entity.keep_alive,
            hidden_tag=entity.hidden_tag,
            fixed_tag=entity.fixed_tag,
            show_parent=entity.show_parent,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name={self.name})>"


# ============ 安全模型 ============


class IPRule(SQLModel, table=True):
    """IP 黑白名单规则实体。"""

    __tablename__ = "sys_ip_rules"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    ip_address: str = Field(max_length=45, index=True)
    rule_type: str = Field(max_length=10)  # "whitelist" 或 "blacklist"
    reason: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    expires_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    def __repr__(self) -> str:
        return f"<IPRule(ip={self.ip_address}, type={self.rule_type})>"


# ============ 部门模型 ============


class Department(SQLModel, table=True):
    """部门实体（树形结构）。"""

    __tablename__ = "sys_departments"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    name: str = Field(max_length=64)  # 部门名称
    parent_id: str | None = Field(default=None, foreign_key="sys_departments.id")  # 父部门ID
    sort: int = Field(default=0)  # 排序号
    principal: str | None = Field(default=None, max_length=50)  # 负责人
    phone: str | None = Field(default=None, max_length=20)  # 联系电话
    email: str | None = Field(default=None, max_length=100)  # 邮箱
    status: int = Field(default=1)  # 状态(0-禁用, 1-启用)
    remark: str | None = Field(default=None, max_length=500)  # 备注
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    updated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()))

    def to_domain(self) -> "DepartmentEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.department import DepartmentEntity

        return DepartmentEntity(id=self.id, name=self.name, parent_id=self.parent_id, sort=self.sort, principal=self.principal, phone=self.phone, email=self.email, status=self.status, remark=self.remark, created_at=self.created_at, updated_at=self.updated_at)

    @classmethod
    def from_domain(cls, entity: "DepartmentEntity") -> "Department":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, name=entity.name, parent_id=entity.parent_id, sort=entity.sort, principal=entity.principal, phone=entity.phone, email=entity.email, status=entity.status, remark=entity.remark, created_at=entity.created_at, updated_at=entity.updated_at)

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name={self.name})>"


# ============ 日志模型 ============


class LoginLog(SQLModel, table=True):
    """登录日志实体。"""

    __tablename__ = "sys_login_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50)  # 用户名
    ip: str | None = Field(default=None, max_length=45)  # IP地址
    address: str | None = Field(default=None, max_length=200)  # 登录地点
    system: str | None = Field(default=None, max_length=100)  # 操作系统
    browser: str | None = Field(default=None, max_length=100)  # 浏览器
    status: int = Field(default=1)  # 登录状态(0-失败, 1-成功)
    behavior: str | None = Field(default=None, max_length=200)  # 行为描述
    login_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    def to_domain(self) -> "LoginLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import LoginLogEntity

        return LoginLogEntity(id=self.id, username=self.username, ip=self.ip, address=self.address, system=self.system, browser=self.browser, status=self.status, behavior=self.behavior, login_time=self.login_time)

    @classmethod
    def from_domain(cls, entity: "LoginLogEntity") -> "LoginLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, username=entity.username, ip=entity.ip, address=entity.address, system=entity.system, browser=entity.browser, status=entity.status, behavior=entity.behavior, login_time=entity.login_time)

    def __repr__(self) -> str:
        return f"<LoginLog(id={self.id}, username={self.username})>"


class OperationLog(SQLModel, table=True):
    """操作日志实体。"""

    __tablename__ = "sys_operation_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    username: str = Field(max_length=50)  # 操作人员
    ip: str | None = Field(default=None, max_length=45)  # IP地址
    address: str | None = Field(default=None, max_length=200)  # 操作地点
    system: str | None = Field(default=None, max_length=100)  # 操作系统
    browser: str | None = Field(default=None, max_length=100)  # 浏览器
    status: int = Field(default=1)  # 操作状态(0-失败, 1-成功)
    summary: str | None = Field(default=None, max_length=200)  # 操作摘要
    module: str | None = Field(default=None, max_length=100)  # 操作模块
    operating_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))

    def to_domain(self) -> "OperationLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import OperationLogEntity

        return OperationLogEntity(id=self.id, username=self.username, ip=self.ip, address=self.address, system=self.system, browser=self.browser, status=self.status, summary=self.summary, module=self.module, operating_time=self.operating_time)

    @classmethod
    def from_domain(cls, entity: "OperationLogEntity") -> "OperationLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(id=entity.id, username=entity.username, ip=entity.ip, address=entity.address, system=entity.system, browser=entity.browser, status=entity.status, summary=entity.summary, module=entity.module, operating_time=entity.operating_time)

    def __repr__(self) -> str:
        return f"<OperationLog(id={self.id}, username={self.username})>"


class SystemLog(SQLModel, table=True):
    """系统日志实体。"""

    __tablename__ = "sys_system_logs"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True, max_length=36)
    level: str | None = Field(default=None, max_length=20)  # 日志级别
    module: str | None = Field(default=None, max_length=100)  # 所属模块
    url: str | None = Field(default=None, max_length=500)  # 请求URL
    method: str | None = Field(default=None, max_length=10)  # 请求方法
    ip: str | None = Field(default=None, max_length=45)  # IP地址
    address: str | None = Field(default=None, max_length=200)  # 请求地点
    system: str | None = Field(default=None, max_length=100)  # 操作系统
    browser: str | None = Field(default=None, max_length=100)  # 浏览器
    takes_time: float | None = Field(default=None)  # 耗时(毫秒)
    request_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    request_body: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 请求体
    response_body: str | None = Field(default=None, sa_column=Column(Text, nullable=True))  # 响应体

    def to_domain(self) -> "SystemLogEntity":
        """将 ORM 模型转换为领域实体。"""
        from src.domain.entities.log import SystemLogEntity

        return SystemLogEntity(id=self.id, level=self.level, module=self.module, url=self.url, method=self.method, ip=self.ip, address=self.address, system=self.system, browser=self.browser, takes_time=self.takes_time, request_time=self.request_time, request_body=self.request_body, response_body=self.response_body)

    @classmethod
    def from_domain(cls, entity: "SystemLogEntity") -> "SystemLog":
        """从领域实体创建 ORM 模型实例。"""
        return cls(
            id=entity.id,
            level=entity.level,
            module=entity.module,
            url=entity.url,
            method=entity.method,
            ip=entity.ip,
            address=entity.address,
            system=entity.system,
            browser=entity.browser,
            takes_time=entity.takes_time,
            request_time=entity.request_time,
            request_body=entity.request_body,
            response_body=entity.response_body,
        )

    def __repr__(self) -> str:
        return f"<SystemLog(id={self.id}, module={self.module})>"


# ============ 角色-菜单关联模型 ============


class RoleMenuLink(SQLModel, table=True):
    """角色-菜单关联表（用于多对多关系）。"""

    __tablename__ = "sys_role_menus"

    role_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_roles.id", ondelete="CASCADE"), primary_key=True))
    menu_id: str = Field(sa_column=Column(String(36), ForeignKey("sys_menus.id", ondelete="CASCADE"), primary_key=True))
