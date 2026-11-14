/** 顶栏通知铃铛：最新公告/通知下拉 + WebSocket 实时推送（对齐 Vue 版 lay-notice） */
import { BellOutlined } from '@ant-design/icons';
import { history } from '@umijs/max';
import { App, Badge, Empty, List, Popover, Tabs, type TabsProps } from 'antd';
import dayjs from 'dayjs';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { getLatestNotices, type NoticeRow } from '@/services/api';
import { realtime } from '@/utils/websocket';

interface ListItem {
  id?: string;
  title: string;
  datetime: string;
  description: string;
}

interface TabItem {
  key: string;
  name: string;
  list: ListItem[];
}

const initialTabs: TabItem[] = [
  { key: '1', name: '公告', list: [] },
  { key: '2', name: '通知', list: [] },
];

/** 后端公告 DTO → 列表项归一化（历史拉取与实时推送共用） */
function toItem(n: NoticeRow): ListItem {
  return {
    id: n.id,
    title: n.title,
    description: n.content || '',
    datetime: n.createdTime
      ? dayjs(n.createdTime).format('YYYY-MM-DD HH:mm')
      : '',
  };
}

export const NoticeDropdown: React.FC = () => {
  const { message } = App.useApp();
  const [tabs, setTabs] = useState<TabItem[]>(initialTabs);
  const [open, setOpen] = useState(false);
  const [bellRing, setBellRing] = useState(false);
  const bellTimer = useRef<number | null>(null);

  /** 拉取最新启用公告填充下拉（公告 noticeType=2 → tab1，通知 noticeType=1 → tab2） */
  const fetchNotices = useCallback(async () => {
    try {
      const rows = await getLatestNotices();
      if (!Array.isArray(rows)) return;
      setTabs((prev) =>
        prev.map((tab) => ({
          ...tab,
          list:
            tab.key === '1'
              ? rows.filter((n) => n.noticeType === 2).map(toItem)
              : rows.filter((n) => n.noticeType === 1).map(toItem),
        })),
      );
    } catch {
      // 铃铛取数失败静默降级，不影响布局
    }
  }, []);

  /** 实时推送：插入对应 tab 顶部 + 弹窗提示 + 铃铛摇晃 */
  const onRealtimeNotice = useCallback(
    (payload: unknown) => {
      const n = payload as NoticeRow | undefined;
      if (!n) return;
      const key = n.noticeType === 2 ? '1' : '2';
      setTabs((prev) =>
        prev.map((tab) =>
          tab.key === key ? { ...tab, list: [toItem(n), ...tab.list] } : tab,
        ),
      );
      message.warning(
        `${n.noticeType === 2 ? '公告' : '通知'}：${n.title ?? ''}`,
      );
      // 触发一次摇晃动画：先 false 再 true 以重新触发 CSS 动画
      setBellRing(false);
      requestAnimationFrame(() => {
        setBellRing(true);
        if (bellTimer.current !== null) window.clearTimeout(bellTimer.current);
        bellTimer.current = window.setTimeout(() => setBellRing(false), 1000);
      });
    },
    [message],
  );

  useEffect(() => {
    void fetchNotices();
    realtime.on('notice', onRealtimeNotice);
    return () => {
      realtime.off('notice', onRealtimeNotice);
      if (bellTimer.current !== null) window.clearTimeout(bellTimer.current);
    };
  }, [fetchNotices, onRealtimeNotice]);

  /** 当前 tab 清空（对齐 Vue 的「标记已读」为本地清空） */
  const markAsRead = (activeKey: string) => {
    setTabs((prev) =>
      prev.map((tab) => (tab.key === activeKey ? { ...tab, list: [] } : tab)),
    );
  };

  const totalCount = tabs.reduce((sum, t) => sum + t.list.length, 0);

  const renderList = (tab: TabItem, activeKey: string) =>
    tab.list.length === 0 ? (
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description="暂无数据"
        style={{ padding: '24px 0', width: 280 }}
      />
    ) : (
      <>
        <List
          style={{ width: 330 }}
          dataSource={tab.list.slice(0, 10)}
          renderItem={(item) => (
            <List.Item style={{ padding: '10px 8px' }}>
              <List.Item.Meta
                title={<span style={{ fontSize: 14 }}>{item.title}</span>}
                description={
                  <span style={{ fontSize: 12, color: 'rgba(0,0,0,0.45)' }}>
                    {item.datetime}
                    {item.description ? ` · ${item.description}` : ''}
                  </span>
                }
              />
            </List.Item>
          )}
        />
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            padding: '6px 8px',
            borderTop: '1px solid rgba(5,5,5,0.06)',
          }}
        >
          <a onClick={() => markAsRead(activeKey)} style={{ fontSize: 13 }}>
            清空{tab.name}
          </a>
          <a
            onClick={() => {
              setOpen(false);
              history.push('/system/notice');
            }}
            style={{ fontSize: 13 }}
          >
            查看更多
          </a>
        </div>
      </>
    );

  const items: TabsProps['items'] = tabs.map((tab) => ({
    key: tab.key,
    label: `${tab.name}${tab.list.length > 0 ? `(${tab.list.length})` : ''}`,
    children: renderList(tab, tab.key),
  }));

  return (
    <Popover
      content={
        <Tabs defaultActiveKey="1" items={items} style={{ minHeight: 220 }} />
      }
      trigger="click"
      placement="bottomRight"
      arrow={false}
      open={open}
      onOpenChange={setOpen}
    >
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 36,
          height: 36,
          cursor: 'pointer',
          borderRadius: 8,
        }}
        onClick={() => setOpen(!open)}
      >
        <Badge count={totalCount} size="small" overflowCount={99}>
          <BellOutlined
            className={bellRing ? 'notice-bell-ring' : undefined}
            style={{ fontSize: 18, color: 'rgba(0,0,0,0.65)' }}
          />
        </Badge>
      </span>
    </Popover>
  );
};
