"""应用层 - 仪表盘统计聚合的数据传输对象。

字段命名沿用 log_dto / monitor_dto 惯例：直接使用 camelCase 字段名
（项目 DTO 对 N815 有豁免，前端 JSON 契约为准）。
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DashboardTotalsDTO(BaseModel):
    """核心资源总数（仪表盘统计卡片）"""

    users: int = Field(default=0, description="用户总数")
    roles: int = Field(default=0, description="角色总数")
    menus: int = Field(default=0, description="菜单总数")
    depts: int = Field(default=0, description="部门总数")
    posts: int = Field(default=0, description="岗位总数")
    online: int = Field(default=0, description="当前在线会话数")


class DashboardTodayStatsDTO(BaseModel):
    """今日业务量统计"""

    loginCount: int = Field(default=0, description="今日成功登录次数")
    opCount: int = Field(default=0, description="今日操作日志条数")


class LoginTrendPointDTO(BaseModel):
    """登录趋势单日数据点"""

    date: str = Field(description="日期文本（MM-DD）")
    count: int = Field(default=0, description="当日成功登录次数")


class OpDistributionItemDTO(BaseModel):
    """操作日志模块分布单项"""

    module: str = Field(description="模块名（None 归并为「未知」）")
    count: int = Field(default=0, description="近 7 天该模块操作次数")


class DashboardRecentLogDTO(BaseModel):
    """仪表盘最近操作日志行（瘦身后仅保留列表展示所需字段）"""

    id: str
    module: str | None = None
    method: str | None = None
    path: str | None = None
    ipaddress: str | None = None
    creator: str = Field(default="", description="操作人用户名（creator_id 批量映射，查不到为空串）")
    statusCode: int | None = None
    createdTime: datetime | None = None

    model_config = {"from_attributes": True}


class DashboardStatsDTO(BaseModel):
    """仪表盘统计聚合响应（GET /api/system/dashboard/stats 的 data 结构）"""

    totals: DashboardTotalsDTO = Field(default_factory=DashboardTotalsDTO)
    todayStats: DashboardTodayStatsDTO = Field(default_factory=DashboardTodayStatsDTO)
    loginTrend: list[LoginTrendPointDTO] = Field(default_factory=list, description="近 7 天登录趋势（含今日，升序）")
    opDistribution: list[OpDistributionItemDTO] = Field(default_factory=list, description="近 7 天操作模块分布 TOP 8")
    recentLogs: list[DashboardRecentLogDTO] = Field(default_factory=list, description="最近 10 条操作日志")
