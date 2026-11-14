/** 岗位管理页面 */
import { PlusOutlined } from '@ant-design/icons';
import {
  type ActionType,
  type ProColumns,
  ProTable,
} from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  App,
  Button,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Switch,
  Tag,
} from 'antd';
import { useRef, useState } from 'react';
import {
  batchDeletePosts,
  createPost,
  deletePost,
  getPosts,
  type PostPayload,
  type PostRow,
  updatePost,
} from '@/services/api';

/** 岗位表单值（isActive 由 Switch 提供，为 boolean） */
interface PostFormValues {
  postCode: string;
  postName: string;
  postSort?: number;
  isActive: boolean;
  remark?: string;
}

export default function PostPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  // 按钮级权限：超管直接放行（与 access.ts 的 isAdmin 口径一致），普通用户按权限码判断
  const can = (code: string): boolean =>
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes(code) ?? false);

  const actionRef = useRef<ActionType | undefined>(undefined);
  const [form] = Form.useForm<PostFormValues>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<PostRow | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [selectedIds, setSelectedIds] = useState<React.Key[]>([]);

  function openCreateModal(): void {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openEditModal(row: PostRow): void {
    setEditing(row);
    form.setFieldsValue({
      postCode: row.postCode,
      postName: row.postName,
      postSort: row.postSort,
      isActive: row.isActive === 1,
      remark: row.remark ?? '',
    });
    setModalOpen(true);
  }

  async function handleSubmit(): Promise<void> {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSubmitting(true);
    try {
      const payload: PostPayload = {
        postCode: values.postCode,
        postName: values.postName,
        postSort: values.postSort,
        isActive: values.isActive ? 1 : 0,
        remark: values.remark,
      };
      if (editing) {
        await updatePost(editing.id, payload);
        message.success('更新成功');
      } else {
        await createPost(payload);
        message.success('创建成功');
      }
      setModalOpen(false);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '操作失败');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(row: PostRow): Promise<void> {
    try {
      await deletePost(row.id);
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
      const count = await batchDeletePosts(selectedIds.map(String));
      message.success(`已删除 ${count} 个岗位`);
      setSelectedIds([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批量删除失败');
    }
  }

  const columns: ProColumns<PostRow>[] = [
    { title: '岗位编码', dataIndex: 'postCode', ellipsis: true },
    { title: '岗位名称', dataIndex: 'postName', ellipsis: true },
    { title: '排序', dataIndex: 'postSort', width: 80, search: false },
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
    { title: '备注', dataIndex: 'remark', ellipsis: true, search: false },
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
        can('post:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            编辑
          </a>
        ) : null,
        can('post:delete') ? (
          <Popconfirm
            key="delete"
            title={`确定删除岗位【${record.postName}】吗？`}
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
      <ProTable<PostRow>
        headerTitle="岗位管理"
        actionRef={actionRef}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        columns={columns}
        rowSelection={
          can('post:delete')
            ? {
                selectedRowKeys: selectedIds,
                onChange: (keys) => setSelectedIds(keys),
              }
            : undefined
        }
        tableAlertOptionRender={() =>
          can('post:delete') ? (
            <Popconfirm
              title={`确定删除选中的 ${selectedIds.length} 个岗位吗？`}
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
          const page = await getPosts({
            pageNum: Number(current) || 1,
            pageSize: Number(pageSize) || 10,
            ...filters,
          });
          return { data: page.list, success: true, total: page.total };
        }}
        toolBarRender={() => [
          can('post:add') ? (
            <Button
              key="create"
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateModal}
            >
              新增岗位
            </Button>
          ) : null,
        ]}
      />
      <Modal
        title={editing ? '编辑岗位' : '新增岗位'}
        open={modalOpen}
        confirmLoading={submitting}
        forceRender
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ isActive: true, postSort: 0 }}
        >
          <Form.Item
            name="postCode"
            label="岗位编码"
            rules={[{ required: true, message: '请输入岗位编码' }]}
          >
            <Input placeholder="请输入岗位编码" />
          </Form.Item>
          <Form.Item
            name="postName"
            label="岗位名称"
            rules={[{ required: true, message: '请输入岗位名称' }]}
          >
            <Input placeholder="请输入岗位名称" />
          </Form.Item>
          <Form.Item name="postSort" label="排序">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="isActive" label="是否启用" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item name="remark" label="备注">
            <Input.TextArea rows={2} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
