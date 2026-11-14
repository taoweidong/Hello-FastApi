import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { App, Popconfirm } from 'antd';
import { useRef } from 'react';
import { forceOffline, getOnlineUsers, type OnlineRow } from '@/services/api';

/** 在线用户：分页列表 + 强制下线（按 monitor:manage 权限码显隐） */
export default function OnlinePage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const canOffline =
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes('monitor:manage') ?? false);
  const actionRef = useRef<ActionType | undefined>(undefined);

  async function handleForceOffline(record: OnlineRow): Promise<void> {
    try {
      await forceOffline(record.id);
      message.success(`已将用户「${record.username}」强制下线`);
      actionRef.current?.reload();
    } catch (error) {
      message.error((error as Error).message || '强制下线失败');
    }
  }

  const columns: ProColumns<OnlineRow>[] = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    {
      title: '登录 IP',
      dataIndex: 'ip',
      key: 'ip',
      search: false,
      render: (_, record) => record.ip ?? '-',
    },
    { title: '浏览器', dataIndex: 'browser', key: 'browser', search: false },
    { title: '操作系统', dataIndex: 'system', key: 'system', search: false },
    {
      title: '登录时间',
      dataIndex: 'loginTime',
      key: 'loginTime',
      search: false,
    },
    {
      title: '过期时间',
      dataIndex: 'expiresAt',
      key: 'expiresAt',
      search: false,
    },
    {
      title: '操作',
      key: 'action',
      valueType: 'option',
      fixed: 'right',
      width: 120,
      search: false,
      render: (_, record) =>
        canOffline ? (
          <Popconfirm
            title={`是否强制下线${record.username}？`}
            onConfirm={() => void handleForceOffline(record)}
          >
            <a style={{ color: '#ff4d4f' }}>强退</a>
          </Popconfirm>
        ) : (
          <span>-</span>
        ),
    },
  ];

  return (
    <ProTable<OnlineRow>
      headerTitle="在线用户"
      rowKey="id"
      actionRef={actionRef}
      columns={columns}
      cardBordered
      search={{ labelWidth: 'auto' }}
      pagination={{ defaultPageSize: 10, showSizeChanger: true }}
      request={async (params) => {
        const page = await getOnlineUsers({
          pageNum: params.current ?? 1,
          pageSize: params.pageSize ?? 10,
          username: params.username,
        });
        return { data: page.list, success: true, total: page.total };
      }}
    />
  );
}
