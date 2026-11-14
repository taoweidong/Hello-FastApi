/** 系统配置管理页面 */
import { PlusOutlined } from '@ant-design/icons';
import {
  type ActionType,
  type ProColumns,
  ProTable,
} from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { App, Button, Form, Input, Modal, Popconfirm, Switch, Tag } from 'antd';
import { useRef, useState } from 'react';
import {
  type ConfigPayload,
  type ConfigRow,
  createConfig,
  deleteConfig,
  getConfigs,
  updateConfig,
} from '@/services/api';

/** 配置表单值（isActive 由 Switch 提供，为 boolean） */
interface ConfigFormValues {
  key: string;
  value: string;
  isActive: boolean;
  description?: string;
}

export default function ConfigPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  // 按钮级权限：超管直接放行（与 access.ts 的 isAdmin 口径一致），普通用户按权限码判断
  const can = (code: string): boolean =>
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes(code) ?? false);

  const actionRef = useRef<ActionType | undefined>(undefined);
  const [form] = Form.useForm<ConfigFormValues>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<ConfigRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function openCreateModal(): void {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openEditModal(row: ConfigRow): void {
    setEditing(row);
    form.setFieldsValue({
      key: row.key,
      value: row.value,
      isActive: row.isActive === 1,
      description: row.description ?? '',
    });
    setModalOpen(true);
  }

  async function handleSubmit(): Promise<void> {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSubmitting(true);
    try {
      const payload: ConfigPayload = {
        key: values.key,
        value: values.value,
        isActive: values.isActive ? 1 : 0,
        description: values.description,
      };
      if (editing) {
        await updateConfig(editing.id, payload);
        message.success('更新成功');
      } else {
        await createConfig(payload);
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

  async function handleDelete(row: ConfigRow): Promise<void> {
    try {
      await deleteConfig(row.id);
      message.success('删除成功');
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除失败');
    }
  }

  const columns: ProColumns<ConfigRow>[] = [
    { title: '配置键', dataIndex: 'key', ellipsis: true },
    { title: '配置值', dataIndex: 'value', ellipsis: true, search: false },
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
    { title: '描述', dataIndex: 'description', ellipsis: true, search: false },
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
        can('config:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            编辑
          </a>
        ) : null,
        can('config:delete') ? (
          <Popconfirm
            key="delete"
            title={`确定删除配置【${record.key}】吗？`}
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
      <ProTable<ConfigRow>
        headerTitle="系统配置管理"
        actionRef={actionRef}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        columns={columns}
        request={async (params) => {
          const { current, pageSize, ...filters } = params as Record<
            string,
            number | string | undefined
          >;
          const page = await getConfigs({
            pageNum: Number(current) || 1,
            pageSize: Number(pageSize) || 10,
            ...filters,
          });
          return { data: page.list, success: true, total: page.total };
        }}
        toolBarRender={() => [
          can('config:add') ? (
            <Button
              key="create"
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateModal}
            >
              新增配置
            </Button>
          ) : null,
        ]}
      />
      <Modal
        title={editing ? '编辑配置' : '新增配置'}
        open={modalOpen}
        confirmLoading={submitting}
        forceRender
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form form={form} layout="vertical" initialValues={{ isActive: true }}>
          <Form.Item
            name="key"
            label="配置键"
            rules={[{ required: true, message: '请输入配置键' }]}
          >
            <Input placeholder="请输入配置键" disabled={!!editing} />
          </Form.Item>
          <Form.Item
            name="value"
            label="配置值"
            rules={[{ required: true, message: '请输入配置值' }]}
          >
            <Input.TextArea rows={3} placeholder="请输入配置值" />
          </Form.Item>
          <Form.Item name="isActive" label="是否启用" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="请输入描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
