"""DTO package."""

from src.application.dto.auth_dto import (
    LoginDTO,
    RegisterDTO,
    RefreshTokenDTO,
    UserInfoDTO,
    TokenResponseDTO,
    LoginResponseDTO,
)
from src.application.dto.user_dto import (
    UserCreateDTO,
    UserUpdateDTO,
    UserResponseDTO,
    UserListQueryDTO,
    ChangePasswordDTO,
    ResetPasswordDTO,
    UpdateStatusDTO,
    BatchDeleteDTO,
)
from src.application.dto.rbac_dto import (
    RoleCreateDTO,
    RoleUpdateDTO,
    RoleResponseDTO,
    RoleListQueryDTO,
    PermissionCreateDTO,
    PermissionResponseDTO,
    PermissionListQueryDTO,
    AssignRoleDTO,
    AssignPermissionsDTO,
)
from src.application.dto.menu_dto import (
    MenuCreateDTO,
    MenuUpdateDTO,
    MenuResponseDTO,
)
from src.application.dto.department_dto import (
    DepartmentCreateDTO,
    DepartmentUpdateDTO,
    DepartmentResponseDTO,
    DepartmentListQueryDTO,
)
from src.application.dto.log_dto import (
    LoginLogListQueryDTO,
    LoginLogResponseDTO,
    OperationLogListQueryDTO,
    OperationLogResponseDTO,
    SystemLogListQueryDTO,
    SystemLogResponseDTO,
    SystemLogDetailDTO,
    BatchDeleteLogDTO,
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
