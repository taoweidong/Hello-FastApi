"""岗位管理路由模块。

提供岗位的增删改查及用户岗位查询功能。
路由前缀: /api/system/post
"""

from classy_fastapi import Routable, delete, get, post, put
from fastapi import Depends

from src.api.common import list_response, success_response
from src.api.common.response_schemas import ApiResponse, PaginatedResponse
from src.api.dependencies import get_current_active_user, get_post_service, require_permission
from src.application.dto.post_dto import PostCreateDTO, PostListQueryDTO, PostUpdateDTO
from src.application.dto.user_dto import BatchDeleteDTO
from src.application.services.post_service import PostService
from src.domain.entities.user import UserEntity


class PostRouter(Routable):
    """岗位管理路由类，提供岗位增删改查功能。"""

    @post("", response_model=PaginatedResponse[dict])
    async def get_list(
        self,
        query: PostListQueryDTO,
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("post:view")),
    ) -> dict:
        """获取岗位列表（分页）。"""
        posts, total = await service.get_posts(query)
        return list_response(
            list_data=[p.model_dump() for p in posts], total=total, page_size=query.pageSize, current_page=query.pageNum
        )

    @get("/options", response_model=ApiResponse[list[dict]])
    async def get_options(
        self, _: UserEntity = Depends(get_current_active_user), service: PostService = Depends(get_post_service)
    ) -> dict:
        """获取启用岗位下拉选项（仅需登录，供用户表单选择）。"""
        options = await service.get_active_post_options()
        return success_response(data=options)

    @get("/user/{user_id}", response_model=ApiResponse[list[str]])
    async def get_user_posts(
        self,
        user_id: str,
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("user:view")),
    ) -> dict:
        """获取用户已分配的岗位 ID 列表。"""
        post_ids = await service.get_user_post_ids(user_id)
        return success_response(data=post_ids)

    @post("/create", response_model=ApiResponse[dict])
    async def create_post(
        self,
        dto: PostCreateDTO,
        current_user: UserEntity = Depends(get_current_active_user),
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("post:add")),
    ) -> dict:
        """创建岗位。"""
        post = await service.create_post(dto, current_user)
        return success_response(data=post.model_dump(), message="创建成功", code=201)

    @post("/batch-delete", response_model=ApiResponse[dict])
    async def batch_delete_posts(
        self,
        dto: BatchDeleteDTO,
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("post:delete")),
    ) -> dict:
        """批量删除岗位。"""
        result = await service.batch_delete_posts(dto.ids)
        return success_response(data=result, message="批量删除成功")

    @get("/{post_id}", response_model=ApiResponse[dict])
    async def get_post(
        self,
        post_id: str,
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("post:view")),
    ) -> dict:
        """获取岗位详情。"""
        post = await service.get_post(post_id)
        return success_response(data=post.model_dump())

    @put("/{post_id}", response_model=ApiResponse[dict])
    async def update_post(
        self,
        post_id: str,
        dto: PostUpdateDTO,
        current_user: UserEntity = Depends(get_current_active_user),
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("post:edit")),
    ) -> dict:
        """更新岗位。"""
        post = await service.update_post(post_id, dto, current_user)
        return success_response(data=post.model_dump(), message="更新成功")

    @delete("/{post_id}", response_model=ApiResponse[None])
    async def delete_post(
        self,
        post_id: str,
        service: PostService = Depends(get_post_service),
        _: dict = Depends(require_permission("post:delete")),
    ) -> dict:
        """删除岗位。"""
        await service.delete_post(post_id)
        return success_response(message="删除成功")
