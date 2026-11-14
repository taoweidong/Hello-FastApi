import type {
  Settings as LayoutSettings,
  MenuDataItem,
} from '@ant-design/pro-components';
import type { RequestConfig, RunTimeLayoutConfig } from '@umijs/max';
import { history, Link } from '@umijs/max';
import {
  type AsyncRouteNode,
  getAsyncRoutes,
  getMine,
  type MineInfo,
} from '@/services/api';
import defaultSettings from '../config/defaultSettings';
import { AvatarDropdown } from './components/RightContent/AvatarDropdown';
import { LangDropdown } from './components/RightContent/LangDropdown';
import { NoticeDropdown } from './components/RightContent/NoticeDropdown';
import { errorConfig } from './requestErrorConfig';
import { realtime } from './utils/websocket';

const loginPath = '/user/login';

export interface InitialState {
  settings?: Partial<LayoutSettings>;
  currentUser?: MineInfo;
  permissions?: string[];
  menus?: AsyncRouteNode[];
  loading?: boolean;
  settingDrawerOpen?: boolean;
  fetchUserInfo?: () => Promise<MineInfo | undefined>;
}

/** 启动时：拉取当前用户 + 动态路由（与 Vue 版 onMounted 语义一致） */
export async function getInitialState(): Promise<InitialState> {
  const fetchUserInfo = async (): Promise<MineInfo | undefined> => {
    try {
      return await getMine();
    } catch {
      history.replace(loginPath);
      return undefined;
    }
  };

  const { location } = history;
  if (location.pathname !== loginPath) {
    try {
      const currentUser = await fetchUserInfo();
      const routes = await getAsyncRoutes();
      // 从 localStorage 读取登录时存储的权限码
      let permissions: string[] = [];
      try {
        const raw = localStorage.getItem('react-admin-auth');
        if (raw) {
          const parsed = JSON.parse(raw);
          permissions = parsed?.state?.permissions ?? [];
        }
      } catch {
        /* 忽略 */
      }
      // 已登录：建立 WebSocket 实时通道（页面刷新场景；SPA 登录后在登录页触发）
      if (currentUser) realtime.start();
      return {
        fetchUserInfo,
        currentUser,
        permissions,
        menus: routes,
        settings: defaultSettings as Partial<LayoutSettings>,
      };
    } catch {
      history.replace(loginPath);
      return {
        fetchUserInfo,
        settings: defaultSettings as Partial<LayoutSettings>,
      };
    }
  }
  return {
    fetchUserInfo,
    settings: defaultSettings as Partial<LayoutSettings>,
  };
}

// ProLayout 运行时配置（Ant Design Pro 布局能力）
export const layout: RunTimeLayoutConfig = ({ initialState }) => {
  const menus = (initialState?.menus ?? []) as AsyncRouteNode[];
  function toMenuData(nodes: AsyncRouteNode[]): MenuDataItem[] {
    return nodes
      .filter((n) => n.meta?.showLink !== false)
      .map((n) => ({
        path: n.path,
        name: n.meta?.title ?? n.name,
        children: n.children ? toMenuData(n.children) : undefined,
      }));
  }
  return {
    title: 'PureAdmin React',
    logo: 'https://pure-admin.github.io/vue-pure-admin/logo.svg',
    layout: 'mix',
    fixSiderbar: true,
    fixedHeader: true,
    menu: { locale: false },
    menuDataRender: () => toMenuData(menus),
    menuItemRender: (item, dom) => <Link to={item.path ?? '/'}>{dom}</Link>,
    // 顶栏动作区：语言切换 + 通知铃铛（对齐 Vue 版 navbar）
    actionsRender: () => [
      <LangDropdown key="lang" />,
      <NoticeDropdown key="notice" />,
    ],
    avatarProps: {
      title:
        initialState?.currentUser?.nickname ||
        initialState?.currentUser?.username ||
        'Admin',
      src: initialState?.currentUser?.avatar || undefined,
      render: (_props, dom) => <AvatarDropdown>{dom}</AvatarDropdown>,
    },
    menuFooterRender: () => (
      <div
        style={{ textAlign: 'center', fontSize: 12, color: 'rgba(0,0,0,0.45)' }}
      >
        Hello-FastApi · React 管理端
      </div>
    ),
  };
};

// 请求配置（baseURL 由 UmiJS proxy 处理，Authorization 由 request 拦截器注入）
export const request: RequestConfig = errorConfig;
