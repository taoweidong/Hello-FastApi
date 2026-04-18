"""字典管理路由模块。

提供字典的增删改查功能。
路由直接挂在 /api/system 路径下（无额外前缀）。
"""

from classy_fastapi import Routable, delete, post, put
from fastapi import Body, Depends

from src.api.common import success_response
from src.api.dependencies import get_dictionary_service, require_permission
from src.application.dto.dictionary_dto import DictionaryCreateDTO, DictionaryListQueryDTO, DictionaryUpdateDTO
from src.application.services.dictionary_service import DictionaryService


class DictionaryRouter(Routable):
    """字典管理路由类，提供字典增删改查功能。"""

    @post("/dictionary")
    async def get_dictionary_list(self, data: dict = Body(default={}), service: DictionaryService = Depends(get_dictionary_service), _: dict = Depends(require_permission("dictionary:view"))) -> dict:
        """获取字典列表（扁平结构）。"""
        query = DictionaryListQueryDTO(name=data.get("name"), isActive=data.get("isActive"))
        dictionaries = await service.get_dictionaries(query)
        dict_list = [d.model_dump() for d in dictionaries]
        return success_response(data=dict_list)

    @post("/dictionary/getByName")
    async def get_dictionary_by_name(self, data: dict = Body(default={}), service: DictionaryService = Depends(get_dictionary_service), _: dict = Depends(require_permission("dictionary:view"))) -> dict:
        """根据字典名称查询字典项。"""
        name = data.get("name", "")
        dictionaries = await service.get_dictionary_by_name(name)
        dict_list = [d.model_dump() for d in dictionaries]
        return success_response(data=dict_list)

    @post("/dictionary/create")
    async def create_dictionary(self, dto: DictionaryCreateDTO, service: DictionaryService = Depends(get_dictionary_service), _: dict = Depends(require_permission("dictionary:add"))) -> dict:
        """创建字典。"""
        dictionary = await service.create_dictionary(dto)
        return success_response(data={"id": dictionary.id, "name": dictionary.name}, message="创建成功", code=201)

    @put("/dictionary/{dict_id}")
    async def update_dictionary(self, dict_id: str, dto: DictionaryUpdateDTO, service: DictionaryService = Depends(get_dictionary_service), _: dict = Depends(require_permission("dictionary:edit"))) -> dict:
        """更新字典。"""
        dictionary = await service.update_dictionary(dict_id, dto)
        return success_response(data={"id": dictionary.id, "name": dictionary.name}, message="更新成功")

    @delete("/dictionary/{dict_id}")
    async def delete_dictionary(self, dict_id: str, service: DictionaryService = Depends(get_dictionary_service), _: dict = Depends(require_permission("dictionary:delete"))) -> dict:
        """删除字典。"""
        await service.delete_dictionary(dict_id)
        return success_response(message="删除成功")
