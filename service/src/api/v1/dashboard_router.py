"""仪表盘路由模块。

提供仪表盘统计聚合接口（统计卡片 / 登录趋势 / 操作分布 / 最近日志）。
登录即可访问，无特殊权限要求（与 /mine 等登录态接口对齐，走
``get_current_active_user``）。
"""

from classy_fastapi import Routable, get
from fastapi import Depends

from src.api.common.response_builder import success_response
from src.api.common.response_schemas import ApiResponse
from src.api.dependencies import get_current_active_user
from src.api.dependencies.dashboard_service import get_dashboard_service
from src.application.dto.dashboard_dto import DashboardStatsDTO
from src.application.services.dashboard_service import DashboardService
from src.domain.entities.user import UserEntity


class DashboardRouter(Routable):
    """仪表盘路由类，提供统计聚合查询接口。"""

    @get("/dashboard/stats", response_model=ApiResponse[DashboardStatsDTO])
    async def get_dashboard_stats(
        self,
        _: UserEntity = Depends(get_current_active_user),
        service: DashboardService = Depends(get_dashboard_service),
    ) -> dict:
        """获取仪表盘统计聚合数据（登录即可访问）。

        返回 totals（六类资源总数，含在线会话数）、todayStats、近 7 天
        登录趋势、操作模块分布 TOP 8 与最近 10 条操作日志；
        聚合结果带 60s 短缓存（dashboard:stats）。
        """
        data = await service.get_dashboard_stats()
        return success_response(data=data)
