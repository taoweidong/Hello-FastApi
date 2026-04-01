"""部门领域 - 仓储接口。

定义部门仓储的抽象接口，遵循依赖倒置原则。
返回类型使用 Any 作为过渡方案，因为上层代码仍大量使用 ORM 模型属性。
"""

from abc import ABC, abstractmethod
from typing import Any


class DepartmentRepositoryInterface(ABC):
    """部门的抽象仓储接口。"""

    @abstractmethod
    async def get_all(self, session: Any) -> list[Any]:
        """获取所有部门。

        Args:
            session: 数据库会话

        Returns:
            部门列表
        """
        ...

    @abstractmethod
    async def get_by_id(self, dept_id: str, session: Any) -> Any | None:
        """根据 ID 获取部门。

        Args:
            dept_id: 部门ID
            session: 数据库会话

        Returns:
            部门对象或 None
        """
        ...

    @abstractmethod
    async def get_by_name(self, name: str, session: Any) -> Any | None:
        """根据名称获取部门。

        Args:
            name: 部门名称
            session: 数据库会话

        Returns:
            部门对象或 None
        """
        ...

    @abstractmethod
    async def get_by_parent_id(self, parent_id: str | None, session: Any) -> list[Any]:
        """根据父部门 ID 获取子部门。

        Args:
            parent_id: 父部门ID，None 表示获取顶级部门
            session: 数据库会话

        Returns:
            子部门列表
        """
        ...

    @abstractmethod
    async def create(self, department: Any, session: Any) -> Any:
        """创建部门。

        Args:
            department: 部门对象
            session: 数据库会话

        Returns:
            创建后的部门对象
        """
        ...

    @abstractmethod
    async def update(self, department: Any, session: Any) -> Any:
        """更新部门。

        Args:
            department: 部门对象
            session: 数据库会话

        Returns:
            更新后的部门对象
        """
        ...

    @abstractmethod
    async def delete(self, dept_id: str, session: Any) -> bool:
        """删除部门。

        Args:
            dept_id: 部门ID
            session: 数据库会话

        Returns:
            是否删除成功
        """
        ...

    @abstractmethod
    async def count(self, name: str | None = None, status: int | None = None, session: Any = None) -> int:
        """获取部门总数。

        Args:
            name: 部门名称过滤
            status: 状态过滤
            session: 数据库会话

        Returns:
            部门总数
        """
        ...
