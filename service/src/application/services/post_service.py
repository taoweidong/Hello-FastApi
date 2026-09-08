"""应用层 - 岗位服务。"""

from src.application.dto.post_dto import PostCreateDTO, PostListQueryDTO, PostResponseDTO, PostUpdateDTO
from src.domain.entities.post import PostEntity
from src.domain.entities.user import UserEntity
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories.post_repository import PostRepositoryInterface


class PostService:
    """岗位操作的应用服务。"""

    def __init__(self, post_repo: PostRepositoryInterface):
        self.post_repo = post_repo

    async def create_post(self, dto: PostCreateDTO, current_user: UserEntity) -> PostResponseDTO:
        """创建岗位（编码唯一校验）。"""
        existing = await self.post_repo.get_by_code(dto.postCode)
        if existing:
            raise ConflictError(f"岗位编码 '{dto.postCode}' 已存在")

        post_entity = PostEntity.create_new(
            post_code=dto.postCode, post_name=dto.postName, post_sort=dto.postSort, remark=dto.remark or ""
        )
        post_entity.is_active = dto.isActive
        post_entity.creator_id = current_user.id
        created = await self.post_repo.create(post_entity)
        return self._to_response(created)

    async def get_post(self, post_id: str) -> PostResponseDTO:
        """根据ID获取岗位。"""
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            raise NotFoundError(f"岗位 ID '{post_id}' 不存在")
        return self._to_response(post)

    async def get_posts(self, query: PostListQueryDTO) -> tuple[list[PostResponseDTO], int]:
        """获取岗位列表。"""
        total = await self.post_repo.count(post_code=query.postCode, post_name=query.postName, is_active=query.isActive)
        posts = await self.post_repo.get_all(
            page_num=query.pageNum,
            page_size=query.pageSize,
            post_code=query.postCode,
            post_name=query.postName,
            is_active=query.isActive,
        )
        return [self._to_response(p) for p in posts], total

    async def get_active_post_options(self) -> list[dict]:
        """获取启用岗位下拉选项（供用户表单选择）。"""
        posts = await self.post_repo.get_all_active()
        return [{"id": p.id, "postCode": p.post_code, "postName": p.post_name, "postSort": p.post_sort} for p in posts]

    async def get_user_post_ids(self, user_id: str) -> list[str]:
        """获取用户已分配的岗位 ID 列表。"""
        return await self.post_repo.get_post_ids_by_user(user_id)

    async def update_post(self, post_id: str, dto: PostUpdateDTO, current_user: UserEntity) -> PostResponseDTO:
        """更新岗位。"""
        post = await self.post_repo.get_by_id(post_id)
        if post is None:
            raise NotFoundError(f"岗位 ID '{post_id}' 不存在")

        if dto.postCode is not None:
            existing = await self.post_repo.get_by_code(dto.postCode)
            if existing and existing.id != post_id:
                raise ConflictError(f"岗位编码 '{dto.postCode}' 已存在")

        post.update_info(
            post_code=dto.postCode,
            post_name=dto.postName,
            post_sort=dto.postSort,
            is_active=dto.isActive,
            remark=dto.remark,
        )
        post.modifier_id = current_user.id
        updated = await self.post_repo.update(post)
        return self._to_response(updated)

    async def delete_post(self, post_id: str) -> bool:
        """删除岗位。"""
        if not await self.post_repo.delete(post_id):
            raise NotFoundError(f"岗位 ID '{post_id}' 不存在")
        return True

    async def batch_delete_posts(self, post_ids: list[str]) -> dict:
        """批量删除岗位。"""
        deleted_count = await self.post_repo.batch_delete(post_ids)
        return {"deleted_count": deleted_count, "total_requested": len(post_ids)}

    @staticmethod
    def _to_response(post: PostEntity) -> PostResponseDTO:
        """将岗位实体转换为响应 DTO。"""
        return PostResponseDTO(
            id=post.id,
            postCode=post.post_code,
            postName=post.post_name,
            postSort=post.post_sort,
            isActive=post.is_active,
            remark=post.remark,
            creatorId=post.creator_id,
            modifierId=post.modifier_id,
            createdTime=post.created_time,
            updatedTime=post.updated_time,
        )
