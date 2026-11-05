"""岗位应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.post_service import PostService


async def get_post_service(repos: RepoBundle = Depends(get_repositories)) -> PostService:
    """获取岗位服务实例（仓储来自请求级仓储束，事务约定见 repositories.py）。"""
    return PostService(post_repo=repos.post)
