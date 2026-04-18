"""DTO package."""

from src.application.dto.auth_dto import LoginDTO, LoginResponseDTO, RefreshTokenDTO, RegisterDTO, TokenResponseDTO, UserInfoDTO
from src.application.dto.department_dto import DepartmentCreateDTO, DepartmentListQueryDTO, DepartmentResponseDTO, DepartmentUpdateDTO
from src.application.dto.dictionary_dto import DictionaryCreateDTO, DictionaryListQueryDTO, DictionaryResponseDTO, DictionaryUpdateDTO
from src.application.dto.log_dto import BatchDeleteLogDTO, LoginLogListQueryDTO, LoginLogResponseDTO, OperationLogListQueryDTO, OperationLogResponseDTO
from src.application.dto.menu_dto import MenuCreateDTO, MenuMetaDTO, MenuResponseDTO, MenuUpdateDTO
from src.application.dto.role_dto import AssignMenusDTO, AssignRoleDTO, RoleCreateDTO, RoleListQueryDTO, RoleResponseDTO, RoleUpdateDTO
from src.application.dto.system_config_dto import SystemConfigCreateDTO, SystemConfigListQueryDTO, SystemConfigResponseDTO, SystemConfigUpdateDTO
from src.application.dto.user_dto import BatchDeleteDTO, ChangePasswordDTO, ResetPasswordDTO, UpdateStatusDTO, UserCreateDTO, UserListQueryDTO, UserResponseDTO, UserUpdateDTO

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
    # role_dto
    "RoleCreateDTO",
    "RoleUpdateDTO",
    "RoleResponseDTO",
    "RoleListQueryDTO",
    "AssignRoleDTO",
    "AssignMenusDTO",
    # menu_dto
    "MenuCreateDTO",
    "MenuUpdateDTO",
    "MenuResponseDTO",
    "MenuMetaDTO",
    # department_dto
    "DepartmentCreateDTO",
    "DepartmentUpdateDTO",
    "DepartmentResponseDTO",
    "DepartmentListQueryDTO",
    # dictionary_dto
    "DictionaryCreateDTO",
    "DictionaryUpdateDTO",
    "DictionaryResponseDTO",
    "DictionaryListQueryDTO",
    # system_config_dto
    "SystemConfigCreateDTO",
    "SystemConfigUpdateDTO",
    "SystemConfigResponseDTO",
    "SystemConfigListQueryDTO",
    # log_dto
    "LoginLogListQueryDTO",
    "LoginLogResponseDTO",
    "OperationLogListQueryDTO",
    "OperationLogResponseDTO",
    "BatchDeleteLogDTO",
]
