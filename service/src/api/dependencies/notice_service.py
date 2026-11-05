"""通知公告应用服务工厂。"""

from fastapi import Depends

from src.api.dependencies.repositories import RepoBundle, get_repositories
from src.application.services.notice_service import NoticeService
from src.domain.services.realtime_port import RealtimePort
from src.infrastructure.realtime.adapter import get_realtime_port


async def get_notice_service(
    repos: RepoBundle = Depends(get_repositories), realtime_port: RealtimePort = Depends(get_realtime_port)
) -> NoticeService:
    """获取通知公告服务实例。

    注入 RealtimePort（依赖倒置）：公告发布/更新时经此端口做实时推送，
    应用层不直接持有 WebSocket 连接管理器。
    """
    return NoticeService(notice_repo=repos.notice, realtime_port=realtime_port)
