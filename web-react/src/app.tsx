import type { Settings as LayoutSettings } from '@ant-design/pro-components';
import type { RequestConfig, RunTimeLayoutConfig } from '@umijs/max';
import { history, Link } from '@umijs/max';
import { App as AntApp } from 'antd';
import defaultSettings from '../config/defaultSettings';
import { errorConfig } from './requestErrorConfig';
import { getMine, getAsyncRoutes, type AsyncRouteNode, type MineInfo } from '@/services/api';

const loginPath = '/user/login';

export interface InitialState {
  settings?: Partial<LayoutSettings>;
  currentUser?: MineInfo;
  permissions?: string[];
  menus?: AsyncRouteNode[];
  loading?: boolean;
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
      return {
        fetchUserInfo,
        currentUser,
        menus: routes,
        settings: defaultSettings as Partial<LayoutSettings>,
      };
    } catch {
      history.replace(loginPath);
      return { fetchUserInfo, settings: defaultSettings as Partial<LayoutSettings> };
    }
  }
  return { fetchUserInfo, settings: defaultSettings as Partial<LayoutSettings> };
}

// ProLayout 运行时配置（Ant Design Pro 布局能力）
export const layout: RunTimeLayoutConfig = ({ initialState }) => {
  const menus = (initialState?.menus ?? []) as AsyncRouteNode[];
  function toMenuData(nodes: AsyncRouteNode[]): MenuDataItem[] {
    return nodes
      .filter(n => n.meta?.showLink !== false)
      .map(n => ({
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
    menuItemRender: (item, dom) => <Link to={item.path}>{dom}</Link>,
    avatarProps: {
      title: initialState?.currentUser?.nickname || initialState?.currentUser?.username || 'Admin',
      render: (_props, dom) => (
        <div onClick={() => history.push('/account-settings')} style={{ cursor: 'pointer' }}>{dom}</div>
      ),
    },
    menuFooterRender: () => <div style={{ textAlign: 'center', fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>Hello-FastApi · React 管理端</div>,
  };
};

// 请求配置（baseURL 由 UmiJS proxy 处理，Authorization 由 request 拦截器注入）
export const request: RequestConfig = errorConfig;
