"""请求级仓储束与聚合工厂。

事务约定（见 ``infrastructure/repositories/base.py`` 模块 docstring）要求同一请求内的
所有仓储共享同一个 ``AsyncSession``——此前由各个服务工厂自觉 ``Repository(db)`` 保证，
约定成立但全靠人肉记忆，新工厂自建 session 会让事务边界静默分裂且无任何报警。

本模块把约定工具化：``get_repositories`` 是组合根里唯一持有 Session 的入口，
服务工厂只接收 ``RepoBundle``。新增仓储时在束里加一个属性即可，
"自建 session 的工厂"在结构上不再可能。
"""

from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from src.infrastructure.database import get_db
from src.infrastructure.repositories.department_repository import DepartmentRepository
from src.infrastructure.repositories.dictionary_repository import DictionaryRepository
from src.infrastructure.repositories.ip_rule_repository import IPRuleRepository
from src.infrastructure.repositories.log_repository import LogRepository
from src.infrastructure.repositories.menu_repository import MenuRepository
from src.infrastructure.repositories.notice_repository import NoticeRepository
from src.infrastructure.repositories.post_repository import PostRepository
from src.infrastructure.repositories.role_repository import RoleRepository
from src.infrastructure.repositories.system_config_repository import SystemConfigRepository
from src.infrastructure.repositories.user_repository import UserRepository


class RepoBundle:
    """绑定在同一请求级 Session 上的全部仓储实现。

    仓储构造只是持有 Session 的轻量动作，因此一次性建好全套；
    束内所有仓储的 ``session`` 属性必然指向同一个对象，这就是请求级单事务的保证。
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user = UserRepository(session)
        self.role = RoleRepository(session)
        self.menu = MenuRepository(session)
        self.department = DepartmentRepository(session)
        self.post = PostRepository(session)
        self.dictionary = DictionaryRepository(session)
        self.log = LogRepository(session)
        self.notice = NoticeRepository(session)
        self.system_config = SystemConfigRepository(session)
        self.ip_rule = IPRuleRepository(session)


async def get_repositories(db: AsyncSession = Depends(get_db)) -> RepoBundle:
    """聚合工厂：以请求级 Session 捆绑全部仓储。

    ``get_db`` 由 FastAPI 按请求缓存，同一请求内多次依赖本工厂拿到的是同一个束，
    与业务仓储共享同一事务边界。
    """
    return RepoBundle(db)
