"""DTO package."""

from src.application.dto.auth_dto import (
    LoginDTO,
    LoginResponseDTO,
    RefreshTokenDTO,
    RegisterDTO,
    TokenResponseDTO,
    UserInfoDTO,
)
from src.application.dto.department_dto import (
    DepartmentCreateDTO,
    DepartmentListQueryDTO,
    DepartmentResponseDTO,
    DepartmentUpdateDTO,
)
from src.application.dto.log_dto import (
    BatchDeleteLogDTO,
    LoginLogListQueryDTO,
    LoginLogResponseDTO,
    OperationLogListQueryDTO,
    OperationLogResponseDTO,
    SystemLogDetailDTO,
    SystemLogListQueryDTO,
    SystemLogResponseDTO,
)
from src.application.dto.menu_dto import MenuCreateDTO, MenuResponseDTO, MenuUpdateDTO
from src.application.dto.rbac_dto import (
    AssignPermissionsDTO,
    AssignRoleDTO,
    PermissionCreateDTO,
    PermissionListQueryDTO,
    PermissionResponseDTO,
    RoleCreateDTO,
    RoleListQueryDTO,
    RoleResponseDTO,
    RoleUpdateDTO,
)
from src.application.dto.user_dto import (
    BatchDeleteDTO,
    ChangePasswordDTO,
    ResetPasswordDTO,
    UpdateStatusDTO,
    UserCreateDTO,
    UserListQueryDTO,
    UserResponseDTO,
    UserUpdateDTO,
)

__all__ = [
    # auth_dto
    "LoginDTO",
    "RegisterDTO",
    "RefreshTokenDTO",
    "UserInfoDTO",
    "TokenResponseDTO",
    "LoginResponseDTO",
    # user_dto
    "UserCreateDTO",
    "UserUpdateDTO",
    "UserResponseDTO",
    "UserListQueryDTO",
    "ChangePasswordDTO",
    "ResetPasswordDTO",
    "UpdateStatusDTO",
    "BatchDeleteDTO",
    # rbac_dto
    "RoleCreateDTO",
    "RoleUpdateDTO",
    "RoleResponseDTO",
    "RoleListQueryDTO",
    "PermissionCreateDTO",
    "PermissionResponseDTO",
    "PermissionListQueryDTO",
    "AssignRoleDTO",
    "AssignPermissionsDTO",
    # menu_dto
    "MenuCreateDTO",
    "MenuUpdateDTO",
    "MenuResponseDTO",
    # department_dto
    "DepartmentCreateDTO",
    "DepartmentUpdateDTO",
    "DepartmentResponseDTO",
    "DepartmentListQueryDTO",
    # log_dto
    "LoginLogListQueryDTO",
    "LoginLogResponseDTO",
    "OperationLogListQueryDTO",
    "OperationLogResponseDTO",
    "SystemLogListQueryDTO",
    "SystemLogResponseDTO",
    "SystemLogDetailDTO",
    "BatchDeleteLogDTO",
]
