/**
 * 后端实体类型定义（与 service/src/application/dto/*_dto.py 的 ResponseDTO 对齐）
 *
 * 目的：消除 API 层的 `any`，让 vue-tsc 真正生效——字段改名/接口变更能在编译期暴露，
 * 而不是等到运行时崩溃。
 *
 * 约定：
 * - 时间字段统一为 string | null（后端 datetime 经 JSON 序列化为字符串）
 * - 树形结构统一使用 children 字段，由前端 handleTree 构造
 */

/** 审计字段（创建人/修改人/时间），几乎所有实体共有 */
export interface AuditFields {
  /** 创建人 ID */
  creatorId?: string | null;
  /** 最后修改人 ID */
  modifierId?: string | null;
  /** 创建时间 */
  createdTime?: string | null;
  /** 更新时间 */
  updatedTime?: string | null;
  /** 备注描述 */
  description?: string | null;
}

/** 树形节点通用字段 */
export interface TreeNode<T> {
  /** 子节点（由前端 handleTree 构造） */
  children?: T[];
}

// ---------------------------------------------------------------- 用户

/** 用户角色摘要 */
export interface UserRoleRef {
  id: string;
  name?: string;
  code?: string;
}

/** 用户实体 */
export interface SystemUser extends AuditFields {
  id: string;
  username: string;
  nickname?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  avatar?: string | null;
  email?: string | null;
  phone?: string | null;
  gender?: number | null;
  /** 是否启用：1 启用 / 0 禁用 */
  isActive?: number;
  /** 是否职员 */
  isStaff?: number;
  /** 数据权限模式 */
  modeType?: number;
  /** 所属部门 ID */
  deptId?: string | null;
  /** 所属角色列表 */
  roles?: UserRoleRef[];
  /** 密码（仅创建时使用，响应中不会返回） */
  password?: string;
}

// ---------------------------------------------------------------- 角色

/** 角色实体 */
export interface SystemRole extends AuditFields {
  id: string;
  name: string;
  code: string;
  /** 是否启用：1 启用 / 0 禁用 */
  isActive?: number;
  /** 关联菜单摘要列表 */
  menus?: Array<Record<string, unknown>>;
  /** 关联的菜单 ID 列表（提交时使用） */
  menuIds?: string[];
  /** 数据权限范围：1-全部 2-自定义 3-本部门 4-本部门及以下 5-仅本人 */
  dataScope?: number;
  /** 自定义数据权限时绑定的部门 ID 列表 */
  deptIds?: string[];
}

// ---------------------------------------------------------------- 菜单

/** 菜单 meta 配置 */
export interface MenuMeta {
  id?: string;
  title?: string | null;
  icon?: string | null;
  rSvgName?: string | null;
  isShowMenu?: number;
  isShowParent?: number;
  isKeepalive?: number;
  frameUrl?: string | null;
  frameLoading?: number;
  transitionEnter?: string | null;
  transitionLeave?: string | null;
  isHiddenTag?: number;
  fixedTag?: number;
  dynamicLevel?: number;
}

/** 菜单实体（目录/页面/按钮权限三类统一模型） */
export interface SystemMenu extends AuditFields, TreeNode<SystemMenu> {
  id: string;
  /** 父菜单 ID，顶级为 null */
  parentId?: string | null;
  /** 菜单类型：0-目录 1-页面 2-按钮权限 */
  menuType?: number;
  /** 菜单名称（唯一，同时作为按钮权限码） */
  name: string;
  /** 路由路径 */
  path?: string | null;
  /** 组件路径 */
  component?: string | null;
  /** 排序号 */
  rank?: number;
  isActive?: number;
  /** HTTP 方法（PERMISSION 类型使用） */
  method?: string | null;
  /** 显示标题 */
  title?: string | null;
  icon?: string | null;
  rSvgName?: string | null;
  /** 菜单 meta 配置 */
  meta?: MenuMeta;
}

// ---------------------------------------------------------------- 部门

/** 部门实体 */
export interface SystemDept extends AuditFields, TreeNode<SystemDept> {
  id: string;
  parentId?: string | null;
  name: string;
  /** 权限模式：0-OR 1-AND */
  modeType?: number;
  /** 部门编码 */
  code?: string;
  rank?: number;
  /** 是否自动绑定角色 */
  autoBind?: number;
  isActive?: number;
}

// ---------------------------------------------------------------- 字典

/** 字典实体 */
export interface SystemDictionary
  extends AuditFields, TreeNode<SystemDictionary> {
  id: string;
  parentId?: string | null;
  name: string;
  /** 显示标签 */
  label?: string;
  /** 字典值 */
  value?: string;
  sort?: number;
  isActive?: number;
}

// ---------------------------------------------------------------- 系统配置

/** 系统配置实体 */
export interface SystemConfig extends AuditFields {
  id: string;
  /** 配置键（唯一） */
  key: string;
  /** 配置值（JSON 字符串） */
  value: string;
  isActive?: number;
  /** 访问级别 */
  access?: number;
  /** 是否继承 */
  inherit?: number;
}

// ---------------------------------------------------------------- IP 规则

/** IP 规则实体 */
export interface IpRule extends AuditFields {
  id: string;
  /** IP 地址或 CIDR 段 */
  ipAddress: string;
  /** 规则类型：blacklist / whitelist */
  ruleType: "blacklist" | "whitelist" | string;
  /** 加入规则的原因 */
  reason?: string;
  /** 是否启用 */
  isActive?: number;
  /** 过期时间 */
  expiresAt?: string | null;
}

// ---------------------------------------------------------------- 日志

/** 登录日志 */
export interface LoginLog extends AuditFields {
  id: string;
  /** 登录状态：1 成功 / 0 失败 */
  status?: number;
  /** 登录类型：0-密码 1-短信 2-OAuth */
  loginType?: number;
  ipaddress?: string | null;
  system?: string | null;
  browser?: string | null;
  agent?: string | null;
  createdTime?: string | null;
}

/** 操作日志 */
export interface OperationLog extends AuditFields {
  id: string;
  /** 操作模块 */
  module?: string | null;
  /** 操作描述 */
  description?: string | null;
  /** HTTP 方法 */
  method?: string | null;
  /** 请求路径 */
  path?: string | null;
  ipaddress?: string | null;
  /** 耗时（毫秒） */
  costTime?: number | null;
  createdTime?: string | null;
}

/** 系统日志 */
export interface SystemLog extends AuditFields {
  id: string;
  /** 日志级别 */
  level?: string | null;
  /** 日志内容 */
  content?: string | null;
  /** 日志来源 */
  source?: string | null;
  createdTime?: string | null;
}

// ---------------------------------------------------------------- 在线用户

/** 在线用户 */
export interface OnlineUser {
  id: string;
  username?: string | null;
  nickname?: string | null;
  ipaddress?: string | null;
  /** 登录时间 */
  loginTime?: string | null;
  /** 最后活跃时间 */
  lastActiveTime?: string | null;
  browser?: string | null;
  system?: string | null;
}

// ---------------------------------------------------------------- 通知公告

/** 通知公告实体 */
export interface SystemNotice extends AuditFields {
  id: string;
  /** 公告标题 */
  title: string;
  /** 公告类型：1-通知 2-公告 */
  noticeType?: number | null;
  /** 是否启用：1 启用 / 0 关闭 */
  isActive?: number | null;
  /** 发布人名称 */
  publisherName?: string | null;
  /** 公告内容 */
  content?: string | null;
}
