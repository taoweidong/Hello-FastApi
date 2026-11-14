/** 通知公告页面 */
import { PlusOutlined } from '@ant-design/icons';
import {
  type ActionType,
  type ProColumns,
  ProTable,
} from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { App, Button, Form, Input, Modal, Popconfirm, Radio, Tag } from 'antd';
import { useRef, useState } from 'react';
import {
  batchDeleteNotices,
  createNotice,
  deleteNotice,
  getNotices,
  type NoticePayload,
  type NoticeRow,
  updateNotice,
} from '@/services/api';

/** 公告表单值 */
interface NoticeFormValues {
  title: string;
  content?: string;
  noticeType: number;
  isActive: number;
}

export default function NoticePage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  // 按钮级权限：超管直接放行（与 access.ts 的 isAdmin 口径一致），普通用户按权限码判断
  const can = (code: string): boolean =>
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes(code) ?? false);

  const actionRef = useRef<ActionType | undefined>(undefined);
  const [form] = Form.useForm<NoticeFormValues>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<NoticeRow | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [selectedIds, setSelectedIds] = useState<React.Key[]>([]);

  function openCreateModal(): void {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openEditModal(row: NoticeRow): void {
    setEditing(row);
    form.setFieldsValue({
      title: row.title,
      content: row.content ?? '',
      noticeType: row.noticeType,
      isActive: row.isActive,
    });
    setModalOpen(true);
  }

  async function handleSubmit(): Promise<void> {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSubmitting(true);
    try {
      const payload: NoticePayload = {
        title: values.title,
        content: values.content,
        noticeType: values.noticeType,
        isActive: values.isActive,
      };
      if (editing) {
        await updateNotice(editing.id, payload);
        message.success('更新成功');
      } else {
        await createNotice(payload);
        message.success('发布成功');
      }
      setModalOpen(false);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '操作失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(row: NoticeRow): Promise<void> {
    try {
      await deleteNotice(row.id);
      message.success('删除成功');
      setSelectedIds((prev) => prev.filter((key) => key !== row.id));
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除失败');
    }
  }

  async function handleBatchDelete(): Promise<void> {
    if (selectedIds.length === 0) return;
    try {
      const count = await batchDeleteNotices(selectedIds.map(String));
      message.success(`已删除 ${count} 条公告`);
      setSelectedIds([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批量删除失败');
    }
  }

  const columns: ProColumns<NoticeRow>[] = [
    { title: '标题', dataIndex: 'title', ellipsis: true },
    {
      title: '类型',
      dataIndex: 'noticeType',
      width: 90,
      search: false,
      render: (_, record) => (
        <Tag color={record.noticeType === 1 ? 'cyan' : 'blue'}>
          {record.noticeType === 1 ? '通知' : '公告'}
        </Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      search: false,
      render: (_, record) => (
        <Tag color={record.isActive === 1 ? 'success' : 'default'}>
          {record.isActive === 1 ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '发布人',
      dataIndex: 'publisherName',
      width: 120,
      ellipsis: true,
      search: false,
    },
    {
      title: '创建时间',
      dataIndex: 'createdTime',
      width: 170,
      valueType: 'dateTime',
      search: false,
    },
    {
      title: '操作',
      valueType: 'option',
      fixed: 'right',
      width: 130,
      render: (_, record) => [
        can('notice:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            编辑
          </a>
        ) : null,
        can('notice:delete') ? (
          <Popconfirm
            key="delete"
            title={`确定删除公告【${record.title}】吗？`}
            onConfirm={() => handleDelete(record)}
          >
            <a style={{ color: '#ff4d4f' }}>删除</a>
          </Popconfirm>
        ) : null,
      ],
    },
  ];

  return (
    <div>
      <ProTable<NoticeRow>
        headerTitle="通知公告"
        actionRef={actionRef}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        columns={columns}
        rowSelection={
          can('notice:delete')
            ? {
                selectedRowKeys: selectedIds,
                onChange: (keys) => setSelectedIds(keys),
              }
            : undefined
        }
        tableAlertOptionRender={() =>
          can('notice:delete') ? (
            <Popconfirm
              title={`确定删除选中的 ${selectedIds.length} 条公告吗？`}
              onConfirm={handleBatchDelete}
            >
              <Button danger size="small">
                批量删除
              </Button>
            </Popconfirm>
          ) : null
        }
        request={async (params) => {
          const { current, pageSize, ...filters } = params as Record<
            string,
            number | string | undefined
          >;
          const page = await getNotices({
            pageNum: Number(current) || 1,
            pageSize: Number(pageSize) || 10,
            ...filters,
          });
          return { data: page.list, success: true, total: page.total };
        }}
        toolBarRender={() => [
          can('notice:add') ? (
            <Button
              key="create"
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateModal}
            >
              发布公告
            </Button>
          ) : null,
        ]}
      />
      <Modal
        title={editing ? '编辑公告' : '发布公告'}
        open={modalOpen}
        confirmLoading={submitting}
        forceRender
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ noticeType: 1, isActive: 1 }}
        >
          <Form.Item
            name="title"
            label="标题"
            rules={[{ required: true, message: '请输入标题' }]}
          >
            <Input placeholder="请输入标题" />
          </Form.Item>
          <Form.Item name="content" label="内容">
            <Input.TextArea rows={5} placeholder="请输入公告内容" />
          </Form.Item>
          <Form.Item name="noticeType" label="类型">
            <Radio.Group
              options={[
                { label: '通知', value: 1 },
                { label: '公告', value: 2 },
              ]}
            />
          </Form.Item>
          <Form.Item name="isActive" label="状态">
            <Radio.Group
              options={[
                { label: '启用', value: 1 },
                { label: '停用', value: 0 },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
