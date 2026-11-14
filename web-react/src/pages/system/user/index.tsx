/** 用户管理页：ProTable 分页列表 + 新增/编辑/分配角色/重置密码 Modal */
import { PlusOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  App,
  Button,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Switch,
  Tag,
  TreeSelect,
} from 'antd';
import { useEffect, useRef, useState } from 'react';
import {
  assignRoles,
  batchDeleteUsers,
  createUser,
  type DeptTreeNode,
  deleteUser,
  getAllRoles,
  getDeptTree,
  getPostOptions,
  getUsers,
  type PostOption,
  type RoleOption,
  resetUserPassword,
  type UserRow,
  updateUser,
  updateUserStatus,
} from '@/services/api';

/** TreeSelect 需要的节点结构 */
interface TreeSelectNode {
  title: string;
  value: string;
  children?: TreeSelectNode[];
}

/** 新增/编辑表单值（type 别名以获得隐式索引签名，可直接传给 Record<string, unknown> 形参） */
type UserFormValues = {
  username?: string;
  password?: string;
  nickname?: string;
  email?: string;
  deptId?: string;
  postIds?: string[];
};

/** 后端部门树 → TreeSelect treeData */
function toTreeSelectData(nodes: DeptTreeNode[]): TreeSelectNode[] {
  return nodes.map((n) => ({
    title: n.name,
    value: n.id,
    children:
      n.children && n.children.length > 0
        ? toTreeSelectData(n.children)
        : undefined,
  }));
}

/** 权限切换后的错误提示文案 */
function errText(e: unknown): string {
  return e instanceof Error ? e.message : '操作失败';
}

export default function UserPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const actionRef = useRef<ActionType>(null);
  const [form] = Form.useForm<UserFormValues>();

  /** 按钮级权限码校验 */
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<UserRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // 下拉数据（部门树 / 岗位）
  const [deptTree, setDeptTree] = useState<DeptTreeNode[]>([]);
  const [postOptions, setPostOptions] = useState<PostOption[]>([]);

  // 分配角色
  const [roleUser, setRoleUser] = useState<UserRow | null>(null);
  const [roleIds, setRoleIds] = useState<string[]>([]);
  const [roleOptions, setRoleOptions] = useState<RoleOption[]>([]);
  const [roleSaving, setRoleSaving] = useState(false);

  // 重置密码
  const [pwdUser, setPwdUser] = useState<UserRow | null>(null);
  const [newPassword, setNewPassword] = useState('');
  const [pwdSaving, setPwdSaving] = useState(false);

  useEffect(() => {
    getDeptTree()
      .then(setDeptTree)
      .catch(() => {
        /* 部门树加载失败时打开弹窗仍可提交，此处静默 */
      });
    getPostOptions()
      .then(setPostOptions)
      .catch(() => {
        /* 岗位选项加载失败时静默 */
      });
  }, []);

  /** 打开新增弹窗 */
  function openCreate(): void {
    setEditing(null);
    form.resetFields();
    setFormOpen(true);
  }

  /** 打开编辑弹窗（不含 password，username 仅展示不可改） */
  function openEdit(row: UserRow): void {
    setEditing(row);
    form.setFieldsValue({
      username: row.username,
      nickname: row.nickname ?? '',
      email: row.email ?? '',
      deptId: row.dept?.id,
    });
    setFormOpen(true);
  }

  /** 提交新增/编辑表单 */
  async function handleFormSubmit(): Promise<void> {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      if (editing) {
        const { username: _u, ...rest } = values;
        await updateUser(editing.id, rest);
        message.success('修改用户成功');
      } else {
        await createUser(values);
        message.success('创建用户成功');
      }
      setFormOpen(false);
      actionRef.current?.reload();
    } catch (e) {
      // 表单校验失败（带 errorFields）不弹错误提示
      const err = e as { errorFields?: unknown };
      if (!err?.errorFields) message.error(errText(e));
    } finally {
      setSubmitting(false);
    }
  }

  /** 打开分配角色弹窗 */
  async function openAssignRoles(row: UserRow): Promise<void> {
    setRoleUser(row);
    setRoleIds(row.roles.map((r) => r.id));
    if (roleOptions.length === 0) {
      try {
        setRoleOptions(await getAllRoles());
      } catch (e) {
        message.error(errText(e));
      }
    }
  }

  /** 保存分配角色 */
  async function handleAssignRoles(): Promise<void> {
    if (!roleUser) return;
    try {
      setRoleSaving(true);
      await assignRoles(roleUser.id, roleIds);
      message.success('分配角色成功');
      setRoleUser(null);
      actionRef.current?.reload();
    } catch (e) {
      message.error(errText(e));
    } finally {
      setRoleSaving(false);
    }
  }

  /** 提交重置密码 */
  async function handleResetPassword(): Promise<void> {
    if (!pwdUser) return;
    if (!newPassword || newPassword.length < 8) {
      message.warning('新密码长度不能少于 8 位');
      return;
    }
    try {
      setPwdSaving(true);
      await resetUserPassword(pwdUser.id, newPassword);
      message.success('重置密码成功');
      setPwdUser(null);
      setNewPassword('');
    } catch (e) {
      message.error(errText(e));
    } finally {
      setPwdSaving(false);
    }
  }

  const columns: ProColumns<UserRow>[] = [
    { title: '用户名', dataIndex: 'username', copyable: true, ellipsis: true },
    {
      title: '昵称',
      dataIndex: 'nickname',
      search: false,
      render: (_, r) => r.nickname ?? '-',
    },
    {
      title: '角色',
      dataIndex: 'roles',
      search: false,
      render: (_, r) =>
        r.roles.length > 0 ? (
          <Space size={4} wrap>
            {r.roles.map((role) => (
              <Tag key={role.id} color="blue">
                {role.name}
              </Tag>
            ))}
          </Space>
        ) : (
          '-'
        ),
    },
    {
      title: '部门',
      dataIndex: 'dept',
      search: false,
      render: (_, r) => r.dept?.name ?? '-',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      search: false,
      render: (_, r) => r.email ?? '-',
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      valueEnum: {
        1: { text: '启用', status: 'Success' },
        0: { text: '禁用', status: 'Error' },
      },
      render: (_, r) => (
        <Switch
          checked={r.isActive === 1}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          disabled={!can('user:edit')}
          onChange={async (checked) => {
            try {
              await updateUserStatus(r.id, checked ? 1 : 0);
              message.success('状态更新成功');
              actionRef.current?.reload();
            } catch (e) {
              message.error(errText(e));
            }
          }}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdTime',
      width: 170,
      search: false,
      render: (_, r) => r.createdTime ?? '-',
    },
    {
      title: '操作',
      valueType: 'option',
      width: 220,
      fixed: 'right',
      render: (_, r) => (
        <Space size={4} wrap>
          {can('user:edit') ? <a onClick={() => openEdit(r)}>编辑</a> : null}
          {can('user:edit') ? (
            <a onClick={() => void openAssignRoles(r)}>分配角色</a>
          ) : null}
          {can('user:edit') ? (
            <a
              onClick={() => {
                setPwdUser(r);
                setNewPassword('');
              }}
            >
              重置密码
            </a>
          ) : null}
          {can('user:delete') ? (
            <Popconfirm
              title="删除用户"
              description={`确定删除用户 ${r.username} 吗？`}
              onConfirm={() => void handleDelete(r.id)}
            >
              <a style={{ color: '#ff4d4f' }}>删除</a>
            </Popconfirm>
          ) : null}
        </Space>
      ),
    },
  ];

  /** 删除单个用户 */
  async function handleDelete(id: string): Promise<void> {
    try {
      await deleteUser(id);
      message.success('删除成功');
      actionRef.current?.reload();
    } catch (e) {
      message.error(errText(e));
    }
  }

  /** 批量删除选中用户 */
  async function handleBatchDelete(): Promise<void> {
    try {
      const count = await batchDeleteUsers(selectedRowKeys.map(String));
      message.success(`已删除 ${count} 个用户`);
      setSelectedRowKeys([]);
      actionRef.current?.reload();
    } catch (e) {
      message.error(errText(e));
    }
  }

  return (
    <>
      <ProTable<UserRow>
        headerTitle="用户列表"
        rowKey="id"
        actionRef={actionRef}
        columns={columns}
        cardBordered
        search={{ labelWidth: 'auto' }}
        rowSelection={{
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys),
        }}
        request={async (params) => {
          // 后端 POST 分页契约：pageNum/pageSize
          const { current, pageSize, ...rest } = params;
          const page = await getUsers({ ...rest, pageNum: current, pageSize });
          return { data: page.list, success: true, total: page.total };
        }}
        toolBarRender={() => [
          can('user:add') ? (
            <Button
              key="create"
              type="primary"
              icon={<PlusOutlined />}
              onClick={openCreate}
            >
              新增用户
            </Button>
          ) : null,
          can('user:delete') ? (
            <Popconfirm
              key="batch"
              title="批量删除"
              description={`确定删除选中的 ${selectedRowKeys.length} 个用户吗？`}
              disabled={selectedRowKeys.length === 0}
              onConfirm={() => void handleBatchDelete()}
            >
              <Button danger disabled={selectedRowKeys.length === 0}>
                批量删除
              </Button>
            </Popconfirm>
          ) : null,
        ]}
      />

      {/* 新增 / 编辑用户（编辑时不显示 password） */}
      <Modal
        title={editing ? `编辑用户：${editing.username}` : '新增用户'}
        open={formOpen}
        confirmLoading={submitting}
        onOk={() => void handleFormSubmit()}
        onCancel={() => setFormOpen(false)}
        destroyOnHidden
        forceRender
      >
        <Form form={form} layout="vertical" initialValues={{ postIds: [] }}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, max: 50, message: '长度 3-50 个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" disabled={!!editing} />
          </Form.Item>
          {!editing ? (
            <Form.Item
              name="password"
              label="密码"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 8, max: 128, message: '长度 8-128 个字符' },
              ]}
            >
              <Input.Password placeholder="请输入密码（至少 8 位）" />
            </Form.Item>
          ) : null}
          <Form.Item name="nickname" label="昵称">
            <Input placeholder="请输入昵称" maxLength={64} />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '邮箱格式不正确' }]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="deptId" label="所属部门">
            <TreeSelect
              allowClear
              placeholder="请选择部门"
              treeData={toTreeSelectData(deptTree)}
              treeDefaultExpandAll
            />
          </Form.Item>
          <Form.Item name="postIds" label="岗位">
            <Select
              mode="multiple"
              allowClear
              placeholder="请选择岗位"
              options={postOptions.map((p) => ({
                label: p.postName,
                value: p.id,
              }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配角色 */}
      <Modal
        title={roleUser ? `分配角色：${roleUser.username}` : '分配角色'}
        open={!!roleUser}
        confirmLoading={roleSaving}
        onOk={() => void handleAssignRoles()}
        onCancel={() => setRoleUser(null)}
        destroyOnHidden
        forceRender
      >
        <Select
          mode="multiple"
          allowClear
          placeholder="请选择角色"
          style={{ width: '100%' }}
          value={roleIds}
          onChange={(v) => setRoleIds(v)}
          options={roleOptions.map((r) => ({ label: r.name, value: r.id }))}
        />
      </Modal>

      {/* 重置密码 */}
      <Modal
        title={pwdUser ? `重置密码：${pwdUser.username}` : '重置密码'}
        open={!!pwdUser}
        confirmLoading={pwdSaving}
        onOk={() => void handleResetPassword()}
        onCancel={() => {
          setPwdUser(null);
          setNewPassword('');
        }}
        destroyOnHidden
        forceRender
      >
        <Input.Password
          placeholder="请输入新密码（至少 8 位）"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
      </Modal>
    </>
  );
}
