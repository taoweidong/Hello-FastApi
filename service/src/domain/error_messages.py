"""领域层 - 错误消息目录。

集中管理所有业务异常的中文消息，避免在 raise 站点散落硬编码字符串。

使用方式::

    from src.domain.error_messages import ErrorMessages as EM
    from src.domain.exceptions import NotFoundError

    raise NotFoundError(EM.USER_NOT_FOUND)
    raise NotFoundError(EM.user_not_found_by_id(user_id))

目录按领域聚合，相同语义的"用户不存在" / "用户不存在或已被禁用"等
历史上散落的不一致描述已统一收敛在此处。
"""


class ErrorMessages:
    """错误消息常量与格式化助手。"""

    # ============ 通用 / 认证 ============

    INVALID_OR_EXPIRED_TOKEN = "无效或已过期的令牌"
    INVALID_TOKEN_TYPE = "无效的令牌类型"
    TOKEN_REVOKED = "令牌已失效"
    INVALID_TOKEN_PAYLOAD = "无效的令牌负载"
    INVALID_REFRESH_TOKEN = "无效的刷新令牌"
    SUPERUSER_REQUIRED = "需要超级用户权限"

    # ============ 用户 ============

    USER_NOT_FOUND = "用户不存在"
    USER_NOT_FOUND_OR_DISABLED = "用户不存在或已被禁用"
    USER_ACCOUNT_DISABLED = "用户账号已被禁用"
    USERNAME_EXISTS = "用户名已存在"
    INVALID_USERNAME_OR_PASSWORD = "用户名或密码错误"
    INCORRECT_OLD_PASSWORD = "旧密码不正确"
    REGISTER_LOAD_FAILED = "注册成功但无法加载用户"

    USERNAME_FORMAT_INVALID = "用户名必须为 3-50 个字符，只允许字母数字和下划线"
    PASSWORD_TOO_SHORT = "密码长度必须至少 8 个字符"
    PASSWORD_REQUIRES_UPPERCASE = "密码必须包含至少一个大写字母"
    PASSWORD_REQUIRES_LOWERCASE = "密码必须包含至少一个小写字母"
    PASSWORD_REQUIRES_DIGIT = "密码必须包含至少一个数字"

    # ============ 角色 ============

    ROLE_ALREADY_ASSIGNED = "角色已分配给该用户"
    ROLE_ASSIGNMENT_NOT_FOUND = "角色分配关系不存在"

    # ============ 菜单 ============

    MENU_NOT_FOUND = "菜单不存在"
    PARENT_MENU_NOT_FOUND = "父菜单不存在"
    MENU_LOAD_FAILED = "菜单创建后无法加载"
    MENU_CIRCULAR_REFERENCE = "不能将菜单设置为自己的子菜单"
    MENU_HAS_CHILDREN = "该菜单下有子菜单，请先删除子菜单"

    # ============ 部门 ============

    DEPARTMENT_NOT_FOUND = "部门不存在"
    PARENT_DEPARTMENT_NOT_FOUND = "父部门不存在"
    DEPARTMENT_NAME_EXISTS = "部门名称已存在"
    DEPARTMENT_CODE_EXISTS = "部门编码已存在"
    DEPARTMENT_CIRCULAR_REFERENCE = "不能将部门设为自己的子部门"
    DEPARTMENT_HAS_CHILDREN = "部门下存在子部门，不能删除"

    # ============ 字典 ============

    DICTIONARY_NOT_FOUND = "字典不存在"
    PARENT_DICTIONARY_NOT_FOUND = "父字典不存在"
    DICTIONARY_CIRCULAR_REFERENCE = "不能将字典设为自己的子字典"
    DICTIONARY_HAS_CHILDREN = "字典下存在子字典，不能删除"

    # ============ IP 规则 ============

    IP_RULE_NOT_FOUND = "IP规则不存在"

    # ============ 格式化助手 ============

    @staticmethod
    def user_not_found_by_id(user_id: str) -> str:
        """按 ID 查不到用户时的标准化消息。"""
        return f"用户 ID '{user_id}' 不存在"

    @staticmethod
    def username_exists(username: str) -> str:
        """用户名已存在（携带具体值，便于前端定位）。"""
        return f"用户名 '{username}' 已存在"

    @staticmethod
    def email_exists(email: str) -> str:
        """邮箱已存在（携带具体值）。"""
        return f"邮箱 '{email}' 已存在"

    @staticmethod
    def role_not_found_by_id(role_id: str) -> str:
        """按 ID 查不到角色时的标准化消息。"""
        return f"角色 ID '{role_id}' 不存在"

    @staticmethod
    def role_name_exists(name: str) -> str:
        """角色名称已存在。"""
        return f"角色名称 '{name}' 已存在"

    @staticmethod
    def role_code_exists(code: str) -> str:
        """角色编码已存在。"""
        return f"角色编码 '{code}' 已存在"
