"""系统监控路由模块。

提供在线用户、地图数据、卡片列表等 stub 接口，
以及服务器监控（CPU/内存/磁盘）与缓存监控（Redis info）接口。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

import random

import redis.asyncio as redis_async
from classy_fastapi import Routable, get, post
from fastapi import Depends
from fastapi.responses import FileResponse

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import require_permission, require_superuser
from src.api.dependencies.monitor_service import get_log_file_service, get_monitor_service, get_redis_or_none
from src.application.dto.monitor_dto import (
    CacheClearDTO,
    CacheGroupDTO,
    CacheInfoDTO,
    ForceOfflineDTO,
    LogFileInfoDTO,
    LogTailDTO,
    OnlineLogsQueryDTO,
    ServerInfoDTO,
)
from src.application.services.log_file_service import LogFileNotFoundError, LogFileService
from src.application.services.monitor_service import MonitorService
from src.domain.exceptions import BusinessError, NotFoundError


class MonitorRouter(Routable):
    """系统监控路由类，提供在线用户、服务器监控、缓存监控等接口。"""

    @get("/server-info", response_model=ApiResponse[ServerInfoDTO])
    async def get_server_info(
        self,
        _: dict = Depends(require_permission("monitor:view")),
        service: MonitorService = Depends(get_monitor_service),
    ) -> dict:
        """获取服务器资源监控数据（CPU/内存/磁盘/系统/进程）。"""
        data = await service.get_server_info()
        return success_response(data=data.model_dump())

    @get("/cache-info", response_model=ApiResponse[CacheInfoDTO])
    async def get_cache_info(
        self,
        _: dict = Depends(require_permission("monitor:view")),
        service: MonitorService = Depends(get_monitor_service),
        redis_client: redis_async.Redis | None = Depends(get_redis_or_none),
    ) -> dict:
        """获取缓存监控数据（Redis info + 键统计），Redis 不可用时降级返回。"""
        data = await service.get_cache_info(redis_client)
        return success_response(data=data.model_dump())

    @get("/cache-groups", response_model=ApiResponse[list[CacheGroupDTO]])
    async def get_cache_groups(
        self,
        _: dict = Depends(require_permission("monitor:view")),
        service: MonitorService = Depends(get_monitor_service),
    ) -> dict:
        """获取缓存分组清单（各业务缓存分组的键数量，Redis 状态监控页）。"""
        groups = await service.get_cache_groups()
        return success_response(data=[g.model_dump() for g in groups])

    @post("/cache-clear", response_model=ApiResponse[dict])
    async def clear_cache_group(
        self,
        dto: CacheClearDTO,
        _: dict = Depends(require_superuser()),
        service: MonitorService = Depends(get_monitor_service),
    ) -> dict:
        """清理指定分组缓存（仅管理员）。

        令牌黑名单组为安全红线不可清理；未知分组返回 400。
        """
        deleted = await service.clear_cache_group(dto)
        return success_response(data={"group": dto.group, "deleted": deleted}, message=f"已清理 {deleted} 个缓存键")

    @post("/cache-clear-all", response_model=ApiResponse[dict])
    async def clear_all_cache(
        self, _: dict = Depends(require_superuser()), service: MonitorService = Depends(get_monitor_service)
    ) -> dict:
        """清理全部可清理业务缓存（仅管理员；不含令牌黑名单与限流计数键）。"""
        deleted = await service.clear_all_cache()
        return success_response(data={"group": "all", "deleted": deleted}, message=f"已清理 {deleted} 个缓存键")

    @post("/online-logs", response_model=PaginatedResponse[dict])
    async def get_online_logs(
        self,
        query: OnlineLogsQueryDTO,
        _: dict = Depends(require_permission("monitor:view")),
        service: MonitorService = Depends(get_monitor_service),
    ) -> dict:
        """获取在线用户会话列表（Redis 实时数据，按用户名过滤 + 分页）。"""
        list_data, total = await service.get_online_logs(query)
        return list_response(list_data=list_data, total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/online-logs/force-offline", response_model=ApiResponse[None])
    async def force_offline(
        self,
        dto: ForceOfflineDTO,
        _: dict = Depends(require_permission("monitor:manage")),
        service: MonitorService = Depends(get_monitor_service),
    ) -> dict:
        """强制下线指定用户会话（删除 Redis 会话并将 Token 加入黑名单）。"""
        success = await service.force_offline(dto.id)
        if not success:
            # 走全局异常体系（HTTP 400），而非 200 + body code=500：
            # 前端拦截器与 HTTP 语义均可正确感知失败
            raise BusinessError("强制下线失败：缓存服务不可用")
        return success_response(message="强制下线成功")

    @get("/get-map-info", response_model=ApiResponse[list[dict]])
    async def get_map_info(self, _: dict = Depends(require_permission("monitor:view"))) -> dict:
        """获取地图数据（stub 数据）。"""
        map_list = []
        drivers = ["张三", "李四", "王五", "赵六", "孙七", "周八", "吴九", "郑十"]
        for _ in range(50):
            lng = round(random.uniform(113.0, 114.1), 4)
            lat = round(random.uniform(34.0, 35.1), 4)
            plate_number = f"豫A{random.randint(10000, 99999)}{random.choice('ABCDEFGHJKLMNPQRSTUVWXYZ')}"
            map_list.append(
                {
                    "plateNumber": plate_number,
                    "driver": random.choice(drivers),
                    "orientation": random.randint(1, 360),
                    "lng": lng,
                    "lat": lat,
                }
            )
        return success_response(data=map_list)

    @post("/get-card-list", response_model=ApiResponse[dict])
    async def get_card_list(self, _: dict = Depends(require_permission("monitor:view"))) -> dict:
        """获取卡片列表（stub 数据）。"""
        card_names = ["SSL证书", "人脸识别", "CVM", "云数据库", "T-Sec 云防火墙"]
        banners = [
            "https://tdesign.gtimg.com/tdesign-pro/cloud-server.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/t-sec.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/ssl.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/cloud-db.jpg",
            "https://tdesign.gtimg.com/tdesign-pro/face-recognition.jpg",
        ]
        descriptions = [
            "SSL证书又叫服务器证书，腾讯云为您提供证书的一站式服务，包括免费、付费证书的申请、管理及部署",
            "基于腾讯优图强大的面部分析技术，提供包括人脸检测与分析、五官定位、人脸搜索、人脸比对、人脸验证等功能",
            "云硬盘为您提供用于CVM的持久性数据块级存储服务。云硬盘中的数据自动地在可用区内以多副本冗余",
            "云数据库MySQL为用户提供安全可靠，性能卓越、易于维护的企业级云数据库服务",
            "腾讯安全云防火墙产品，是腾讯云安全团队结合云原生的优势，自主研发的SaaS化防火墙产品",
        ]
        card_list = []
        for i in range(1, 49):
            card_list.append(
                {
                    "index": i,
                    "isSetup": random.choice([True, False]),
                    "type": random.randint(1, 5),
                    "banner": random.choice(banners),
                    "name": random.choice(card_names),
                    "description": random.choice(descriptions),
                }
            )
        return success_response(data={"list": card_list})

    # ============ 日志文件浏览（仅管理员；远程排查替代登录服务器） ============

    @get("/log-files", response_model=ApiResponse[list[LogFileInfoDTO]])
    async def list_log_files(
        self, _: dict = Depends(require_superuser()), log_file_service: LogFileService = Depends(get_log_file_service)
    ) -> dict:
        """列出日志目录下的全部文件（按修改时间倒序）。

        日志含敏感信息，端点强制超级管理员；未走静态目录匿名挂载。
        """
        files = await log_file_service.list_files()
        return success_response(data=[f.model_dump() for f in files])

    @get("/log-files/{filename}/tail", response_model=ApiResponse[LogTailDTO])
    async def tail_log_file(
        self,
        filename: str,
        lines: int = 200,
        _: dict = Depends(require_superuser()),
        log_file_service: LogFileService = Depends(get_log_file_service),
    ) -> dict:
        """读取日志文件末尾 N 行（默认 200，上限 1000）。"""
        try:
            content = await log_file_service.tail(filename, lines=lines)
        except LogFileNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc
        except ValueError as exc:
            raise BusinessError(str(exc)) from exc
        return success_response(data=LogTailDTO(name=filename, lines=lines, content=content).model_dump())

    @get("/log-files/{filename}", response_class=FileResponse)
    async def download_log_file(
        self,
        filename: str,
        download: bool = False,
        _: dict = Depends(require_superuser()),
        log_file_service: LogFileService = Depends(get_log_file_service),
    ) -> FileResponse:
        """获取日志文件内容（download=true 时作为附件下载）。

        路径穿越/非法文件名在服务层校验，逃逸尝试返回 400。
        """
        try:
            path = await log_file_service.open_path(filename)
        except LogFileNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc
        except ValueError as exc:
            raise BusinessError(str(exc)) from exc
        return FileResponse(path=path, filename=filename if download else None, media_type="text/plain; charset=utf-8")
