/** IP 规则管理页面 */
import { ClearOutlined, PlusOutlined } from '@ant-design/icons';
import {
  type ActionType,
  type ProColumns,
  ProTable,
} from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import { App, Button, Form, Input, Modal, Popconfirm, Select, Tag } from 'antd';
import { useRef, useState } from 'react';
import {
  batchDeleteIpRules,
  clearIpRules,
  createIpRule,
  deleteIpRule,
  getIpRules,
  type IpRulePayload,
  type IpRuleRow,
  updateIpRule,
} from '@/services/api';

/** IP 规则表单值 */
interface IpRuleFormValues {
  ipAddress: string;
  ruleType: string;
  reason?: string;
  isActive: number;
}

/** 规则类型选项 */
const RULE_TYPE_OPTIONS = [
  { label: '黑名单', value: 'blacklist' },
  { label: '白名单', value: 'whitelist' },
];

/** 状态选项 */
const STATUS_OPTIONS = [
  { label: '启用', value: 1 },
  { label: '停用', value: 0 },
];

export default function IpRulePage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  // 按钮级权限：超管直接放行（与 access.ts 的 isAdmin 口径一致），普通用户按权限码判断
  const can = (code: string): boolean =>
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes(code) ?? false);

  const actionRef = useRef<ActionType | undefined>(undefined);
  const [form] = Form.useForm<IpRuleFormValues>();
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<IpRuleRow | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [selectedIds, setSelectedIds] = useState<React.Key[]>([]);

  function openCreateModal(): void {
    setEditing(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openEditModal(row: IpRuleRow): void {
    setEditing(row);
    form.setFieldsValue({
      ipAddress: row.ipAddress,
      ruleType: row.ruleType,
      reason: row.reason ?? '',
      isActive: row.isActive,
    });
    setModalOpen(true);
  }

  async function handleSubmit(): Promise<void> {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSubmitting(true);
    try {
      const payload: IpRulePayload = {
        ipAddress: values.ipAddress,
        ruleType: values.ruleType,
        reason: values.reason,
        isActive: values.isActive,
      };
      if (editing) {
        await updateIpRule(editing.id, payload);
        message.success('更新成功');
      } else {
        await createIpRule(payload);
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

  async function handleDelete(row: IpRuleRow): Promise<void> {
    try {
      await deleteIpRule(row.id);
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
      const count = await batchDeleteIpRules(selectedIds.map(String));
      message.success(`已删除 ${count} 条规则`);
      setSelectedIds([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '批量删除失败');
    }
  }

  async function handleClear(): Promise<void> {
    try {
      const count = await clearIpRules();
      message.success(`已清空 ${count} 条规则`);
      setSelectedIds([]);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '清空失败');
    }
  }

  const columns: ProColumns<IpRuleRow>[] = [
    { title: 'IP地址', dataIndex: 'ipAddress', ellipsis: true, search: false },
    {
      title: '类型',
      dataIndex: 'ruleType',
      width: 100,
      valueType: 'select',
      fieldProps: { options: RULE_TYPE_OPTIONS },
      render: (_, record) => (
        <Tag color={record.ruleType === 'blacklist' ? 'red' : 'green'}>
          {record.ruleType === 'blacklist' ? '黑名单' : '白名单'}
        </Tag>
      ),
    },
    { title: '原因', dataIndex: 'reason', ellipsis: true, search: false },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      valueType: 'select',
      fieldProps: { options: STATUS_OPTIONS },
      render: (_, record) => (
        <Tag color={record.isActive === 1 ? 'success' : 'default'}>
          {record.isActive === 1 ? '启用' : '停用'}
        </Tag>
      ),
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
        can('ip-rule:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            编辑
          </a>
        ) : null,
        can('ip-rule:delete') ? (
          <Popconfirm
            key="delete"
            title={`确定删除 IP【${record.ipAddress}】的规则吗？`}
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
      <ProTable<IpRuleRow>
        headerTitle="IP 规则管理"
        actionRef={actionRef}
        rowKey="id"
        search={{ labelWidth: 'auto' }}
        columns={columns}
        rowSelection={
          can('ip-rule:delete')
            ? {
                selectedRowKeys: selectedIds,
                onChange: (keys) => setSelectedIds(keys),
              }
            : undefined
        }
        tableAlertOptionRender={() =>
          can('ip-rule:delete') ? (
            <Popconfirm
              title={`确定删除选中的 ${selectedIds.length} 条规则吗？`}
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
          const page = await getIpRules({
            pageNum: Number(current) || 1,
            pageSize: Number(pageSize) || 10,
            ...filters,
          });
          return { data: page.list, success: true, total: page.total };
        }}
        toolBarRender={() => [
          can('ip-rule:add') ? (
            <Button
              key="create"
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreateModal}
            >
              新增规则
            </Button>
          ) : null,
          can('ip-rule:delete') ? (
            <Popconfirm
              key="clear"
              title="确定清空全部 IP 规则吗？"
              onConfirm={handleClear}
            >
              <Button danger icon={<ClearOutlined />}>
                一键清空
              </Button>
            </Popconfirm>
          ) : null,
        ]}
      />
      <Modal
        title={editing ? '编辑规则' : '新增规则'}
        open={modalOpen}
        confirmLoading={submitting}
        forceRender
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ ruleType: 'blacklist', isActive: 1 }}
        >
          <Form.Item
            name="ipAddress"
            label="IP地址"
            rules={[{ required: true, message: '请输入IP地址' }]}
          >
            <Input placeholder="请输入IP地址，如 192.168.1.1" />
          </Form.Item>
          <Form.Item
            name="ruleType"
            label="规则类型"
            rules={[{ required: true, message: '请选择规则类型' }]}
          >
            <Select options={RULE_TYPE_OPTIONS} placeholder="请选择规则类型" />
          </Form.Item>
          <Form.Item name="reason" label="原因">
            <Input.TextArea rows={2} placeholder="请输入原因" />
          </Form.Item>
          <Form.Item name="isActive" label="状态">
            <Select options={STATUS_OPTIONS} placeholder="请选择状态" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
