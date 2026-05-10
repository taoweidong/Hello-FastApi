"""用户实体与 DTO 转换映射器。

统一管理用户实体与 DTO 之间的转换逻辑，避免重复代码。
"""

from src.application.dto.user_dto import UserResponseDTO
from src.domain.entities.role import RoleEntity
from src.domain.entities.user import UserEntity


class UserMapper:
    """用户实体与 DTO 转换映射器。"""

    @staticmethod
    def to_response(entity: UserEntity, roles: list[RoleEntity] | None = None) -> UserResponseDTO:
        """将用户实体转换为响应 DTO。

        Args:
            entity: 用户实体
            roles: 角色列表（可选，如果未提供则返回空列表）

        Returns:
            用户响应 DTO
        """
        role_list = []
        if roles:
            role_list = [{"id": role.id, "name": role.name} for role in roles]

        return UserResponseDTO(
            id=entity.id,
            username=entity.username,
            nickname=entity.nickname,
            firstName=entity.first_name,
            lastName=entity.last_name,
            avatar=entity.avatar,
            email=entity.email,
            phone=entity.phone,
            gender=entity.gender,
            isActive=entity.is_active,
            isStaff=entity.is_staff,
            modeType=entity.mode_type,
            roles=role_list,
            creatorId=entity.creator_id,
            modifierId=entity.modifier_id,
            createdTime=entity.created_time,
            updatedTime=entity.updated_time,
            description=entity.description,
        )

    @staticmethod
    def to_response_with_roles(entity: UserEntity, roles: list[RoleEntity]) -> UserResponseDTO:
        """将用户实体和角色列表转换为响应 DTO（用于批量查询优化）。

        Args:
            entity: 用户实体
            roles: 预加载的角色列表

        Returns:
            用户响应 DTO
        """
        return UserMapper.to_response(entity, roles)
