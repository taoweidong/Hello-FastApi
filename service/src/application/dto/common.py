"""跨域共享的公共 DTO 与分页约定。

分页参数此前在 8+ 个 QueryDTO 中逐份手抄（default/ge/le 各写一遍），
统一收敛到 BaseListQueryDTO；上限/默认值调整时只改这一处。
"""

from pydantic import BaseModel, Field

DEFAULT_PAGE_NUM = 1
DEFAULT_PAGE_SIZE = 10
# 单页上限：与仓储层 offset/limit 防御一致，防止超大 page_size 拖库
MAX_PAGE_SIZE = 100


class BaseListQueryDTO(BaseModel):
    """列表查询 DTO 的分页基类。

    各域 QueryDTO 继承本类并只声明业务过滤字段：
        class UserListQueryDTO(BaseListQueryDTO):
            username: str | None = None
    """

    pageNum: int = Field(default=DEFAULT_PAGE_NUM, ge=1, description="页码")
    pageSize: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE, description="每页条数")
