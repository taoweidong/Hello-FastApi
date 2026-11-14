import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { App, Button, Popconfirm, Space, Tag } from 'antd';
import type { Key } from 'react';
import { useRef, useState } from 'react';
import {
  batchDeleteLoginLogs,
  clearLoginLogs,
  getLoginLogs,
  type LoginLogRow,
} from '@/services/api';

/** 登录类型映射（与后端约定：0 密码 / 1 短信 / 2 OAuth） */
const LOGIN_TYPE_MAP: Record<number, string> = {
  0: '密码',
  1: '短信',
  2: 'OAuth',
};

/** 登录日志：分页列表 + 批量删除 + 清空 */
export default function LoginLogPage(): React.ReactNode {
  const { message } = App.useApp();
  const actionRef = useRef<ActionType | undefined>(undefined);
  const [selectedRowKeys, setSelectedRowKeys] = useState<Key[]>([]);

  async function handleBatchDelete(): Promise<void> {
    if (selectedRowKeys.length === 0) {
      return;
    }
    try {
      const count = await batchDeleteLoginLogs(selectedRowKeys.map(String));
      message.success(`已删除 ${count} 条登录日志`);
      setSelectedRowKeys([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error((error as Error).message || '批量删除失败');
    }
  }

  async function handleClear(): Promise<void> {
    try {
      const count = await clearLoginLogs();
      message.success(`已清空 ${count} 条登录日志`);
      setSelectedRowKeys([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error((error as Error).message || '清空登录日志失败');
    }
  }

  const columns: ProColumns<LoginLogRow>[] = [
    // 仅出现在搜索表单中（后端按 username 过滤）
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      hideInTable: true,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      search: false,
      render: (_, record) => (
        <Tag color={record.status === 1 ? 'green' : 'red'}>
          {record.status === 1 ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: 'IP地址',
      dataIndex: 'ipaddress',
      key: 'ipaddress',
      search: false,
    },
    { title: '浏览器', dataIndex: 'browser', key: 'browser', search: false },
    { title: '操作系统', dataIndex: 'system', key: 'system', search: false },
    {
      title: '登录类型',
      dataIndex: 'loginType',
      key: 'loginType',
      width: 100,
      search: false,
      render: (_, record) =>
        LOGIN_TYPE_MAP[record.loginType] ?? record.loginType,
    },
    {
      title: '时间',
      dataIndex: 'createdTime',
      key: 'createdTime',
      search: false,
    },
  ];

  return (
    <ProTable<LoginLogRow>
      headerTitle={
        <Space>
          <Popconfirm
            title={`确定删除选中的 ${selectedRowKeys.length} 条日志吗？`}
            onConfirm={() => void handleBatchDelete()}
            disabled={selectedRowKeys.length === 0}
          >
            <Button danger disabled={selectedRowKeys.length === 0}>
              批量删除
            </Button>
          </Popconfirm>
          <Popconfirm
            title="确定清空全部登录日志吗？"
            description="该操作不可恢复"
            onConfirm={() => void handleClear()}
          >
            <Button danger>清空</Button>
          </Popconfirm>
        </Space>
      }
      rowKey="id"
      actionRef={actionRef}
      columns={columns}
      cardBordered
      search={{ labelWidth: 'auto' }}
      pagination={{ defaultPageSize: 10, showSizeChanger: true }}
      rowSelection={{
        selectedRowKeys,
        onChange: (keys) => setSelectedRowKeys(keys),
      }}
      request={async (params) => {
        const page = await getLoginLogs({
          pageNum: params.current ?? 1,
          pageSize: params.pageSize ?? 10,
          username: params.username,
        });
        return { data: page.list, success: true, total: page.total };
      }}
    />
  );
}
