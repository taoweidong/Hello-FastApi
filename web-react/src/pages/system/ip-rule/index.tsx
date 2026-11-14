/** IP 规则管理页面（对齐 Vue useIpRule：状态开关/过期时间/描述/清空全部） */
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
  DatePicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Switch,
  Tag,
} from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
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
  isActive: boolean;
  expiresAt?: Dayjs | null;
  description?: string;
}

/** 规则类型选项（对齐 Vue IPRuleTypeChoices） */
const RULE_TYPE_OPTIONS = [
  { label: '白名单', value: 'whitelist' },
  { label: '黑名单', value: 'blacklist' },
];

/** 状态选项 */
const STATUS_OPTIONS = [
  { label: '启用', value: 1 },
  { label: '停用', value: 0 },
];

/** 时间格式化（对齐 Vue dayjs YYYY-MM-DD HH:mm:ss） */
function fmtTime(v: string | null | undefined): string {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-';
}

export default function IpRulePage(): React.ReactNode {
  const { message, modal } = App.useApp();
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
      isActive: row.isActive === 1,
      expiresAt: row.expiresAt ? dayjs(row.expiresAt) : null,
      description: row.description ?? '',
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
        reason: values.reason || null,
        isActive: values.isActive === false ? 0 : 1,
        // 留空则永不过期（对齐 Vue value-format YYYY-MM-DDTHH:mm:ss）
        expiresAt: values.expiresAt
          ? values.expiresAt.format('YYYY-MM-DDTHH:mm:ss')
          : null,
        description: values.description || null,
      };
      if (editing) {
        await updateIpRule(editing.id, payload);
        message.success(`成功更新IP规则 ${values.ipAddress}`);
      } else {
        await createIpRule(payload);
        message.success(`成功创建IP规则 ${values.ipAddress}`);
      }
      setModalOpen(false);
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '操作失败');
    } finally {
      setSubmitting(false);
    }
  }

  /** 状态开关（对齐 Vue handleUpdateStatus：失败提示，无确认弹窗） */
  async function handleToggleStatus(
    row: IpRuleRow,
    checked: boolean,
  ): Promise<void> {
    try {
      await updateIpRule(row.id, { isActive: checked ? 1 : 0 });
      message.success('状态更新成功');
      actionRef.current?.reload();
    } catch {
      message.error('状态更新失败');
    }
  }

  async function handleDelete(row: IpRuleRow): Promise<void> {
    try {
      await deleteIpRule(row.id);
      message.success(`已成功删除IP规则 ${row.ipAddress}`);
      setSelectedIds((prev) => prev.filter((key) => key !== row.id));
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除失败');
    }
  }

  /** 批量删除（对齐 Vue useCrudTable.handleBatchDelete：ElMessageBox 确认） */
  function handleBatchDelete(): void {
    const ids = selectedIds.map(String);
    if (ids.length === 0) return;
    modal.confirm({
      title: '系统提示',
      content: `确认要删除选中的 ${ids.length} 条IP规则数据吗?`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await batchDeleteIpRules(ids);
          message.success(`已成功删除 ${ids.length} 条IP规则数据`);
          setSelectedIds([]);
          actionRef.current?.reload();
        } catch (error) {
          message.error(
            error instanceof Error ? error.message : '批量删除失败',
          );
        }
      },
    });
  }

  /** 清空全部（对齐 Vue handleClear：不可逆破坏性操作二次确认） */
  function handleClear(): void {
    modal.confirm({
      title: '清空全部 IP 规则',
      content:
        '将删除全部 IP 规则（含黑名单与白名单），操作不可恢复。是否继续？',
      okText: '确认清空',
      okButtonProps: { danger: true },
      cancelText: '取消',
      onOk: async () => {
        try {
          await clearIpRules();
          message.success('清空成功');
          setSelectedIds([]);
          actionRef.current?.reload();
        } catch {
          message.error('清空失败，请重试');
        }
      },
    });
  }

  const columns: ProColumns<IpRuleRow>[] = [
    { title: 'IP地址', dataIndex: 'ipAddress', ellipsis: true },
    {
      title: '规则类型',
      dataIndex: 'ruleType',
      width: 100,
      valueType: 'select',
      fieldProps: { options: RULE_TYPE_OPTIONS },
      render: (_, record) => (
        <Tag color={record.ruleType === 'whitelist' ? 'green' : 'red'}>
          {record.ruleType === 'whitelist' ? '白名单' : '黑名单'}
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
        <Switch
          checked={record.isActive === 1}
          checkedChildren="启用"
          unCheckedChildren="停用"
          disabled={!can('ip-rule:edit')}
          onChange={(checked) => void handleToggleStatus(record, checked)}
        />
      ),
    },
    {
      title: '过期时间',
      dataIndex: 'expiresAt',
      width: 170,
      search: false,
      render: (_, record) =>
        record.expiresAt ? fmtTime(record.expiresAt) : '永不过期',
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      search: false,
      render: (_, record) => record.description || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'createdTime',
      width: 170,
      search: false,
      render: (_, record) => fmtTime(record.createdTime),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedTime',
      width: 170,
      search: false,
      render: (_, record) => fmtTime(record.updatedTime),
    },
    {
      title: '操作',
      valueType: 'option',
      fixed: 'right',
      width: 130,
      render: (_, record) => [
        can('ip-rule:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            修改
          </a>
        ) : null,
        can('ip-rule:delete') ? (
          <Popconfirm
            key="delete"
            title={`是否确认删除IP为${record.ipAddress}的这条规则`}
            onConfirm={() => void handleDelete(record)}
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
        headerTitle="IP规则管理"
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
        tableAlertOptionRender={
          can('ip-rule:delete')
            ? () => (
                <Button danger size="small" onClick={handleBatchDelete}>
                  批量删除
                </Button>
              )
            : undefined
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
            <Button key="clear" danger onClick={handleClear}>
              清空全部
            </Button>
          ) : null,
        ]}
      />
      <Modal
        title={editing ? '修改IP规则' : '新增IP规则'}
        open={modalOpen}
        confirmLoading={submitting}
        forceRender
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ ruleType: 'blacklist', isActive: true }}
        >
          <Form.Item
            name="ipAddress"
            label="IP地址"
            rules={[{ required: true, message: 'IP地址为必填项' }]}
          >
            <Input placeholder="请输入IP地址" />
          </Form.Item>
          <Form.Item name="ruleType" label="规则类型">
            <Select options={RULE_TYPE_OPTIONS} placeholder="请选择规则类型" />
          </Form.Item>
          <Form.Item name="isActive" label="状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item name="expiresAt" label="过期时间">
            {/* 留空则永不过期 */}
            <DatePicker
              showTime
              format="YYYY-MM-DD HH:mm:ss"
              placeholder="留空则永不过期"
              style={{ width: '100%' }}
            />
          </Form.Item>
          <Form.Item name="reason" label="原因">
            <Input.TextArea rows={2} placeholder="请输入原因" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} placeholder="请输入描述信息" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
