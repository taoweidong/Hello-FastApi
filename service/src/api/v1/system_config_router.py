"""系统配置路由模块。

提供系统配置的增删改查功能。
路由前缀: /api/system/config
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import list_response, success_response
from src.api.dependencies import get_current_active_user, get_system_config_service
from src.application.dto.system_config_dto import SystemConfigCreateDTO, SystemConfigListQueryDTO, SystemConfigUpdateDTO
from src.application.services.system_config_service import SystemConfigService


class SystemConfigRouter(Routable):
    """系统配置路由类，提供系统配置增删改查功能。"""

    @post("")
    async def get_config_list(self, query: SystemConfigListQueryDTO, service: SystemConfigService = Depends(get_system_config_service), current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取系统配置列表（分页）。"""
        configs, total = await service.get_configs(query)
        return list_response(list_data=[c.model_dump() for c in configs], total=total, page_size=query.pageSize, current_page=query.pageNum)

    @post("/create")
    async def create_config(self, dto: SystemConfigCreateDTO, service: SystemConfigService = Depends(get_system_config_service), current_user: dict = Depends(get_current_active_user)) -> dict:
        """创建系统配置。"""
        config = await service.create_config(dto)
        return success_response(data=config, message="创建成功", code=201)

    @get("/{config_id}")
    async def get_config(self, config_id: str, service: SystemConfigService = Depends(get_system_config_service), current_user: dict = Depends(get_current_active_user)) -> dict:
        """获取系统配置详情。"""
        config = await service.get_config(config_id)
        return success_response(data=config)

    @put("/{config_id}")
    async def update_config(self, config_id: str, dto: SystemConfigUpdateDTO, service: SystemConfigService = Depends(get_system_config_service), current_user: dict = Depends(get_current_active_user)) -> dict:
        """更新系统配置。"""
        config = await service.update_config(config_id, dto)
        return success_response(data=config, message="更新成功")

    @delete("/{config_id}")
    async def delete_config(self, config_id: str, service: SystemConfigService = Depends(get_system_config_service), current_user: dict = Depends(get_current_active_user)) -> dict:
        """删除系统配置。"""
        await service.delete_config(config_id)
        return success_response(message="删除成功")
