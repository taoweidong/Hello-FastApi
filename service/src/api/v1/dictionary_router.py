"""字典管理路由模块。

提供字典的增删改查功能。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Body, Depends

from src.api.common import success_response
from src.api.common.response_schemas import ApiResponse
from src.api.dependencies import get_current_active_user, get_dictionary_service, require_permission
from src.application.dto.dictionary_dto import (
    DictionaryCreateDTO,
    DictionaryListQueryDTO,
    DictionaryNameQueryDTO,
    DictionaryUpdateDTO,
)
from src.application.services.dictionary_service import DictionaryService
from src.domain.entities.user import UserEntity


class DictionaryRouter(Routable):
    """字典管理路由类，提供字典增删改查功能。"""

    @post("/dictionary", response_model=ApiResponse[list[dict]])
    async def get_dictionary_list(
        self,
        query: DictionaryListQueryDTO = Body(default=DictionaryListQueryDTO()),
        service: DictionaryService = Depends(get_dictionary_service),
        _: dict = Depends(require_permission("dictionary:view")),
    ) -> dict:
        """获取字典列表（扁平结构）。"""
        dictionaries = await service.get_dictionaries(query)
        dict_list = [d.model_dump() for d in dictionaries]
        return success_response(data=dict_list)

    @post("/dictionary/getByName", response_model=ApiResponse[list[dict]])
    async def get_dictionary_by_name(
        self,
        query: DictionaryNameQueryDTO = Body(default=DictionaryNameQueryDTO()),
        service: DictionaryService = Depends(get_dictionary_service),
        _: dict = Depends(require_permission("dictionary:view")),
    ) -> dict:
        """根据字典名称查询字典项。"""
        dictionaries = await service.get_dictionary_by_name(query.name)
        dict_list = [d.model_dump() for d in dictionaries]
        return success_response(data=dict_list)

    @get("/dictionary/type/{dict_name}", response_model=ApiResponse[list[dict]])
    async def get_dict_items_by_type(
        self,
        dict_name: str,
        _: UserEntity = Depends(get_current_active_user),
        service: DictionaryService = Depends(get_dictionary_service),
    ) -> dict:
        """根据字典类型名称获取启用状态的字典项。

        业务表单联动取数接口：仅需登录即可访问（无需按钮权限），
        返回按 sort 升序的 label/value 列表，底层带 Redis 缓存。
        """
        items = await service.get_dict_items_by_type(dict_name)
        return success_response(data=items)

    @post("/dictionary/create", response_model=ApiResponse[dict])
    async def create_dictionary(
        self,
        dto: DictionaryCreateDTO,
        service: DictionaryService = Depends(get_dictionary_service),
        _: dict = Depends(require_permission("dictionary:add")),
    ) -> dict:
        """创建字典。"""
        dictionary = await service.create_dictionary(dto)
        return success_response(data={"id": dictionary.id, "name": dictionary.name}, message="创建成功", code=201)

    @put("/dictionary/{dict_id}", response_model=ApiResponse[dict])
    async def update_dictionary(
        self,
        dict_id: str,
        dto: DictionaryUpdateDTO,
        service: DictionaryService = Depends(get_dictionary_service),
        _: dict = Depends(require_permission("dictionary:edit")),
    ) -> dict:
        """更新字典。"""
        dictionary = await service.update_dictionary(dict_id, dto)
        return success_response(data={"id": dictionary.id, "name": dictionary.name}, message="更新成功")

    @delete("/dictionary/{dict_id}", response_model=ApiResponse[None])
    async def delete_dictionary(
        self,
        dict_id: str,
        service: DictionaryService = Depends(get_dictionary_service),
        _: dict = Depends(require_permission("dictionary:delete")),
    ) -> dict:
        """删除字典。"""
        await service.delete_dictionary(dict_id)
        return success_response(message="删除成功")
