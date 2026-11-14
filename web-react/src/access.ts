/**
 * @see https://umijs.org/docs/max/access#access
 * 权限模型：登录响应的 permissions 数组即该用户全部权限码（超管为全量）。
 */
export default function access(
  initialState:
    | { currentUser?: AccessUser; permissions?: string[] }
    | undefined,
) {
  const { permissions } = initialState ?? {};
  return {
    /** 按钮级权限码校验 */
    hasPermission: (code: string) => permissions?.includes(code) ?? false,
    /** 超管判定 */
    isAdmin: initialState?.currentUser?.username === 'admin',
  };
}

/** 访问插件使用的最小用户信息（MineInfo 子集） */
interface AccessUser {
  username?: string;
}
