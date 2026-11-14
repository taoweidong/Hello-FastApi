import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { App, Button, Modal, Popconfirm, Space, Tag } from 'antd';
import type { Key } from 'react';
import { useRef, useState } from 'react';
import {
  batchDeleteOperationLogs,
  clearOperationLogs,
  getOperationLogs,
  type OperationLogRow,
} from '@/services/api';

/** HTTP 方法对应的 Tag 颜色 */
const METHOD_COLOR_MAP: Record<string, string> = {
  GET: 'blue',
  POST: 'green',
  PUT: 'orange',
  DELETE: 'red',
};

/** 根据响应码返回 Tag 颜色（2xx 绿 / 4xx 橙 / 5xx 红 / 其他默认） */
function responseCodeColor(code: number | null): string {
  if (code === null || code === undefined) {
    return 'default';
  }
  if (code >= 200 && code < 300) {
    return 'green';
  }
  if (code >= 400 && code < 500) {
    return 'orange';
  }
  if (code >= 500) {
    return 'red';
  }
  return 'default';
}

/** 操作日志：分页列表 + 行点击查看详情 + 批量删除 + 清空 */
export default function OperationLogPage(): React.ReactNode {
  const { message } = App.useApp();
  const actionRef = useRef<ActionType | undefined>(undefined);
  const [selectedRowKeys, setSelectedRowKeys] = useState<Key[]>([]);
  // 当前查看详情的日志（null 表示弹窗关闭）
  const [detail, setDetail] = useState<OperationLogRow | null>(null);

  async function handleBatchDelete(): Promise<void> {
    if (selectedRowKeys.length === 0) {
      return;
    }
    try {
      const count = await batchDeleteOperationLogs(selectedRowKeys.map(String));
      message.success(`已删除 ${count} 条操作日志`);
      setSelectedRowKeys([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error((error as Error).message || '批量删除失败');
    }
  }

  async function handleClear(): Promise<void> {
    try {
      const count = await clearOperationLogs();
      message.success(`已清空 ${count} 条操作日志`);
      setSelectedRowKeys([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error((error as Error).message || '清空操作日志失败');
    }
  }

  const columns: ProColumns<OperationLogRow>[] = [
    { title: '模块', dataIndex: 'module', key: 'module' },
    {
      title: '方法',
      dataIndex: 'method',
      key: 'method',
      width: 90,
      search: false,
      render: (_, record) => (
        <Tag color={METHOD_COLOR_MAP[record.method] ?? 'default'}>
          {record.method}
        </Tag>
      ),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
      search: false,
      ellipsis: true,
      render: (_, record) => (
        <Tag
          color={responseCodeColor(record.responseCode)}
          style={{ maxWidth: '100%' }}
        >
          {record.path || '-'}
        </Tag>
      ),
    },
    {
      title: 'IP地址',
      dataIndex: 'ipaddress',
      key: 'ipaddress',
      width: 130,
      search: false,
    },
    {
      title: '操作概要',
      dataIndex: 'description',
      key: 'description',
      search: false,
      ellipsis: true,
    },
    {
      title: '时间',
      dataIndex: 'createdTime',
      key: 'createdTime',
      width: 170,
      search: false,
    },
  ];

  return (
    <>
      <ProTable<OperationLogRow>
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
              title="确定清空全部操作日志吗？"
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
        onRow={(record) => ({ onClick: () => setDetail(record) })}
        request={async (params) => {
          const page = await getOperationLogs({
            pageNum: params.current ?? 1,
            pageSize: params.pageSize ?? 10,
            module: params.module,
          });
          return { data: page.list, success: true, total: page.total };
        }}
      />

      <Modal
        title="操作日志详情"
        open={detail !== null}
        footer={null}
        width={760}
        onCancel={() => setDetail(null)}
      >
        <pre
          style={{
            maxHeight: 480,
            overflow: 'auto',
            margin: 0,
            padding: 12,
            background: 'rgba(0, 0, 0, 0.02)',
            border: '1px solid #f0f0f0',
            borderRadius: 6,
            fontSize: 12,
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {detail ? JSON.stringify(detail, null, 2) : ''}
        </pre>
      </Modal>
    </>
  );
}
