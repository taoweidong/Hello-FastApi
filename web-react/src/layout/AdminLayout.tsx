import { Suspense, useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { Dropdown, Skeleton } from "antd";
import { ProLayout } from "@ant-design/pro-components";
import type { MenuDataItem } from "@ant-design/pro-components";
import { LogoutOutlined, UserOutlined } from "@ant-design/icons";
import { Link } from "react-router-dom";
import { getAsyncRoutes, logout, type AsyncRouteNode } from "@/api/auth";
import { useAuthStore } from "@/store/auth";
import { mapIcon } from "@/components/icons";

/**
 * 管理端布局：侧边菜单由后端 /get-async-routes 动态下发（与 Vue 版同一端点）。
 * component 字段是 Vue 视图路径，React 版按 path 映射到本工程的页面组件；
 * 尚未迁移的页面渲染"建设中"占位。
 */
export function AdminLayout(): React.ReactNode {
  const navigate = useNavigate();
  const location = useLocation();
  const username = useAuthStore(s => s.username);
  const nickname = useAuthStore(s => s.nickname);
  const avatar = useAuthStore(s => s.avatar);
  const refreshToken = useAuthStore(s => s.refreshToken);
  const clear = useAuthStore(s => s.clear);
  const [routes, setRoutes] = useState<AsyncRouteNode[]>([]);
  const [routesLoading, setRoutesLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    getAsyncRoutes()
      .then(tree => {
        if (!cancelled) setRoutes(tree);
      })
      .catch(() => {
        // 拉取失败保留空菜单，用户可手动刷新重试
      })
      .finally(() => {
        if (!cancelled) setRoutesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // 后端路由树 → ProLayout 菜单数据（过滤 showLink=false）
  function toMenuData(nodes: AsyncRouteNode[]): MenuDataItem[] {
    return nodes
      .filter(node => node.meta?.showLink !== false)
      .map(node => ({
        path: node.path,
        name: node.meta?.title ?? node.name,
        icon: mapIcon(node.meta?.icon),
        children: node.children ? toMenuData(node.children) : undefined
      }));
  }

  const menuData: MenuDataItem[] = [
    { path: "/welcome", name: "首页", icon: undefined },
    ...toMenuData(routes)
  ];

  function handleLogout(): void {
    void logout(refreshToken);
    clear();
    navigate("/login", { replace: true });
  }

  if (routesLoading) {
    return <Skeleton active style={{ padding: 24 }} paragraph={{ rows: 10 }} />;
  }

  return (
    <ProLayout
      title="PureAdmin React"
      logo="https://pure-admin.github.io/vue-pure-admin/logo.svg"
      layout="mix"
      fixSiderbar
      route={{ path: "/", children: menuData }}
      location={{ pathname: location.pathname }}
      menuItemRender={(item, dom) => <Link to={item.path ?? "/"}>{dom}</Link>}
      avatarProps={{
        icon: avatar ? undefined : <UserOutlined />,
        src: avatar || undefined,
        size: "small",
        title: nickname || username,
        render: (_props, dom) => (
          <Dropdown
            menu={{
              items: [
                {
                  key: "logout",
                  icon: <LogoutOutlined />,
                  label: "退出登录",
                  onClick: handleLogout
                }
              ]
            }}
          >
            {dom}
          </Dropdown>
        )
      }}
    >
      <Suspense fallback={<Skeleton active style={{ padding: 24 }} />}>
        <Outlet />
      </Suspense>
    </ProLayout>
  );
}
