import type { ReactNode } from "react";
import {
  ApartmentOutlined,
  AppstoreOutlined,
  BellOutlined,
  BookOutlined,
  DashboardOutlined,
  FileTextOutlined,
  GlobalOutlined,
  HomeOutlined,
  IdcardOutlined,
  MonitorOutlined,
  SafetyOutlined,
  SettingOutlined,
  TableOutlined,
  TeamOutlined,
  ToolOutlined,
  UserOutlined
} from "@ant-design/icons";

/**
 * 动态菜单图标映射：后端下发 iconify 图标名（如 ri:table-line / ep:setting），
 * React 版用 antd 图标做关键词匹配，未命中的回退 AppstoreOutlined。
 */
const ICON_MAP: Array<[string, ReactNode]> = [
  ["home", <HomeOutlined />],
  ["dashboard", <DashboardOutlined />],
  ["user", <UserOutlined />],
  ["team", <TeamOutlined />],
  ["role", <SafetyOutlined />],
  ["menu", <AppstoreOutlined />],
  ["dept", <ApartmentOutlined />],
  ["apartment", <ApartmentOutlined />],
  ["book", <BookOutlined />],
  ["dictionary", <BookOutlined />],
  ["setting", <SettingOutlined />],
  ["config", <ToolOutlined />],
  ["monitor", <MonitorOutlined />],
  ["server", <MonitorOutlined />],
  ["log", <FileTextOutlined />],
  ["table", <TableOutlined />],
  ["example", <TableOutlined />],
  ["notice", <BellOutlined />],
  ["bell", <BellOutlined />],
  ["ip", <GlobalOutlined />],
  ["global", <GlobalOutlined />],
  ["post", <IdcardOutlined />],
  ["idcard", <IdcardOutlined />]
];

export function mapIcon(icon: string | undefined): ReactNode {
  if (!icon) return <AppstoreOutlined />;
  const lower = icon.toLowerCase();
  for (const [keyword, node] of ICON_MAP) {
    if (lower.includes(keyword)) return node;
  }
  return <AppstoreOutlined />;
}

/** 按钮权限：登录响应的 permissions 数组即该用户全部权限码（超管为全量） */
export function hasAuth(permissions: string[], code: string): boolean {
  return permissions.includes(code);
}
