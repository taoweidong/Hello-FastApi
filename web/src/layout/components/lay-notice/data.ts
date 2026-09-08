import { $t } from "@/plugins/i18n";

export interface ListItem {
  id?: string;
  avatar: string;
  title: string;
  datetime: string;
  type: string;
  description: string;
  status?: "primary" | "success" | "warning" | "info" | "danger";
  extra?: string;
}

export interface TabItem {
  key: string;
  name: string;
  list: ListItem[];
  emptyText: string;
}

export const noticesData: TabItem[] = [
  {
    key: "1",
    name: "公告",
    list: [],
    emptyText: $t("status.pureNoNotify")
  },
  {
    key: "2",
    name: "通知",
    list: [],
    emptyText: $t("status.pureNoMessage")
  }
];
