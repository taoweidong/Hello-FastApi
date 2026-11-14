/** 用户管理页：ProTable 分页列表 + 新增/编辑/分配角色/重置密码/上传头像 Modal（对齐 Vue useUser） */
import {
  LockOutlined,
  MoreOutlined,
  PlusOutlined,
  TeamOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  App,
  Avatar,
  Button,
  Dropdown,
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
import dayjs from 'dayjs';
import { useEffect, useRef, useState } from 'react';
import {
  assignRoles,
  batchDeleteUsers,
  createUser,
  type DeptTreeNode,
  deleteUser,
  getAllRoles,
  getDeptTree,
  getDictByType,
  getPostOptions,
  getUserPosts,
  getUserRoleIds,
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
  phone?: string;
  email?: string;
  gender?: number;
  deptId?: string;
  postIds?: string[];
  isActive?: boolean;
  description?: string;
};

/** 性别选项（对齐 Vue form genderOptions：0-男 1-女） */
const GENDER_OPTIONS = [
  { label: '男', value: 0 },
  { label: '女', value: 1 },
];

/** 性别字典兜底（sys_user_sex 未命中时使用，对齐 Vue GenderChoices） */
const GENDER_DICT_FALLBACK = [
  { label: '男', value: '0' },
  { label: '女', value: '1' },
];

/** 默认头像（与 Vue userAvatar 占位一致使用内联 SVG，避免二进制资源依赖） */
const DEFAULT_AVATAR =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" fill="#d9e2ec"/><circle cx="32" cy="24" r="12" fill="#94a3b8"/><path d="M10 58c0-12 10-20 22-20s22 8 22 20" fill="#94a3b8"/></svg>',
  );

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

/** 时间格式化（对齐 Vue dayjs YYYY-MM-DD HH:mm:ss） */
function fmtTime(v: string | null | undefined): string {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-';
}

/** 手机号脱敏：下标 3-6 打码（对齐 Vue hideTextAtIndex(phone, { start: 3, end: 6 })） */
function maskPhone(phone: string): string {
  const chars = phone.split('');
  for (let i = 3; i <= 6 && i < chars.length; i += 1) chars[i] = '*';
  return chars.join('');
}

/** 字典项取标签（对齐 Vue dictLabel） */
function dictLabel(
  options: Array<{ label: string; value: string }>,
  value: number | null | undefined,
): string {
  if (value === null || value === undefined) return '未知';
  const hit = options.find((o) => o.value === String(value));
  return hit ? hit.label : '未知';
}

/** 权限切换后的错误提示文案 */
function errText(e: unknown): string {
  return e instanceof Error ? e.message : '操作失败';
}

/** 手机号格式校验（对齐 Vue isPhone） */
const PHONE_PATTERN = /^1[3-9]\d{9}$/;

export default function UserPage(): React.ReactNode {
  const { message, modal } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const actionRef = useRef<ActionType>(null);
  const [form] = Form.useForm<UserFormValues>();

  /** 按钮级权限码校验 */
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<UserRow | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [pwdForm] = Form.useForm<{ newPassword: string }>();

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // 下拉数据（部门树 / 岗位 / 角色 / 性别字典）
  const [deptTree, setDeptTree] = useState<DeptTreeNode[]>([]);
  const [postOptions, setPostOptions] = useState<PostOption[]>([]);
  const [roleOptions, setRoleOptions] = useState<RoleOption[]>([]);
  const [genderDict, setGenderDict] = useState(GENDER_DICT_FALLBACK);

  // 分配角色
  const [roleUser, setRoleUser] = useState<UserRow | null>(null);
  const [roleIds, setRoleIds] = useState<string[]>([]);
  const [roleSaving, setRoleSaving] = useState(false);

  // 重置密码
  const [pwdUser, setPwdUser] = useState<UserRow | null>(null);
  const [pwdSaving, setPwdSaving] = useState(false);

  // 上传头像（与 Vue handleUpload 一致：裁剪预览占位，确认后仅刷新列表）
  const [avatarUser, setAvatarUser] = useState<UserRow | null>(null);

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
    getAllRoles()
      .then(setRoleOptions)
      .catch(() => {
        /* 角色列表加载失败时分配角色弹窗内重试，此处静默 */
      });
    getDictByType('sys_user_sex')
      .then((items) => {
        if (items.length > 0) setGenderDict(items);
      })
      .catch(() => {
        /* 字典取数失败时使用本地兜底 */
      });
  }, []);

  /** 打开新增弹窗 */
  function openCreate(): void {
    setEditing(null);
    form.resetFields();
    setFormOpen(true);
  }

  /** 打开编辑弹窗（username 仅展示不可改：后端 UserUpdateDTO 不含 username；回填已分配岗位） */
  async function openEdit(row: UserRow): Promise<void> {
    setEditing(row);
    form.setFieldsValue({
      username: row.username,
      nickname: row.nickname ?? '',
      phone: row.phone ?? '',
      email: row.email ?? '',
      gender: row.gender ?? undefined,
      deptId: row.dept?.id,
      description: row.description ?? '',
    });
    setFormOpen(true);
    try {
      const postIds = await getUserPosts(row.id);
      form.setFieldsValue({ postIds });
    } catch {
      form.setFieldsValue({ postIds: [] });
    }
  }

  /** 提交新增/编辑表单 */
  async function handleFormSubmit(): Promise<void> {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      // 空值转 null 的映射对齐 Vue openDialog 的 payload 构造
      const payload: Record<string, unknown> = {
        nickname: values.nickname || null,
        email: values.email || null,
        phone: values.phone || null,
        gender: values.gender ?? null,
        deptId: values.deptId || null,
        postIds: values.postIds ?? [],
        description: values.description || null,
      };
      if (editing) {
        // 编辑态 isActive 不在表单中展示，取行数据原值（对齐 Vue 行为）
        payload.isActive = editing.isActive;
        const { username: _u, ...rest } = values;
        await updateUser(editing.id, { ...payload, ...rest });
        message.success(`成功更新用户 ${values.username}`);
      } else {
        payload.username = values.username;
        payload.password = values.password;
        payload.isActive = values.isActive === false ? 0 : 1;
        await createUser(payload);
        message.success(`成功创建用户 ${values.username}`);
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

  /** 状态切换（对齐 Vue onChange：先确认，再调用接口） */
  function handleToggleStatus(row: UserRow, checked: boolean): void {
    const next = checked ? 1 : 0;
    modal.confirm({
      title: '系统提示',
      content: `确认要${checked ? '启用' : '停用'} ${row.username} 用户吗?`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await updateUserStatus(row.id, next);
          message.success('已成功修改用户状态');
          actionRef.current?.reload();
        } catch {
          message.error('修改用户状态失败');
        }
      },
    });
  }

  /** 打开分配角色弹窗：角色 ID 以后端接口回显为准（对齐 Vue handleRole） */
  async function openAssignRoles(row: UserRow): Promise<void> {
    setRoleUser(row);
    setRoleIds([]);
    if (roleOptions.length === 0) {
      try {
        setRoleOptions(await getAllRoles());
      } catch (e) {
        message.error(errText(e));
      }
    }
    try {
      setRoleIds(await getUserRoleIds(row.id));
    } catch (e) {
      message.error(errText(e));
    }
  }

  /** 保存分配角色 */
  async function handleAssignRoles(): Promise<void> {
    if (!roleUser) return;
    try {
      setRoleSaving(true);
      await assignRoles(roleUser.id, roleIds);
      message.success(`已成功为用户 ${roleUser.username} 分配角色`);
      setRoleUser(null);
      actionRef.current?.reload();
    } catch {
      message.error('分配角色失败');
    } finally {
      setRoleSaving(false);
    }
  }

  /** 提交重置密码 */
  async function handleResetPassword(): Promise<void> {
    if (!pwdUser) return;
    try {
      const { newPassword } = await pwdForm.validateFields();
      setPwdSaving(true);
      await resetUserPassword(pwdUser.id, newPassword);
      message.success(`已成功重置 ${pwdUser.username} 用户的密码`);
      setPwdUser(null);
      actionRef.current?.reload();
    } catch (e) {
      const err = e as { errorFields?: unknown };
      if (!err?.errorFields) message.error('重置密码失败');
    } finally {
      setPwdSaving(false);
    }
  }

  /** 删除单个用户 */
  async function handleDelete(row: UserRow): Promise<void> {
    try {
      await deleteUser(row.id);
      message.success(`已成功删除用户 ${row.username}`);
      actionRef.current?.reload();
    } catch (e) {
      message.error(errText(e));
    }
  }

  /** 批量删除选中用户（对齐 Vue onbatchDel：ElMessageBox 确认） */
  function handleBatchDelete(): void {
    const ids = selectedRowKeys.map(String);
    if (ids.length === 0) return;
    modal.confirm({
      title: '系统提示',
      content: `确认要删除选中的 ${ids.length} 个用户吗?`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await batchDeleteUsers(ids);
          message.success(`已成功删除 ${ids.length} 个用户`);
          setSelectedRowKeys([]);
          actionRef.current?.reload();
        } catch (e) {
          message.error(errText(e));
        }
      },
    });
  }

  const columns: ProColumns<UserRow>[] = [
    {
      title: '用户编号',
      dataIndex: 'id',
      width: 90,
      search: false,
    },
    {
      title: '用户头像',
      dataIndex: 'avatar',
      width: 90,
      search: false,
      render: (_, r) => <Avatar src={r.avatar || DEFAULT_AVATAR} size={32} />,
    },
    { title: '用户名称', dataIndex: 'username', ellipsis: true },
    {
      title: '用户昵称',
      dataIndex: 'nickname',
      search: false,
      ellipsis: true,
      render: (_, r) => r.nickname ?? '-',
    },
    {
      title: '性别',
      dataIndex: 'gender',
      width: 80,
      search: false,
      render: (_, r) => (
        <Tag color={r.gender === 1 ? 'red' : 'default'}>
          {dictLabel(genderDict, r.gender)}
        </Tag>
      ),
    },
    {
      title: '部门',
      dataIndex: 'dept',
      search: false,
      ellipsis: true,
      render: (_, r) => r.dept?.name ?? '-',
    },
    {
      title: '手机号码',
      dataIndex: 'phone',
      ellipsis: true,
      render: (_, r) => (r.phone ? maskPhone(r.phone) : '-'),
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      search: false,
      ellipsis: true,
      render: (_, r) => r.email ?? '-',
    },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      valueEnum: {
        1: { text: '已开启', status: 'Success' },
        0: { text: '已关闭', status: 'Error' },
      },
      render: (_, r) => (
        <Switch
          checked={r.isActive === 1}
          checkedChildren="已启用"
          unCheckedChildren="已停用"
          disabled={!can('user:edit')}
          onChange={(checked) => handleToggleStatus(r, checked)}
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdTime',
      width: 170,
      search: false,
      render: (_, r) => fmtTime(r.createdTime),
    },
    {
      title: '描述',
      dataIndex: 'description',
      search: false,
      ellipsis: true,
      render: (_, r) => r.description ?? '-',
    },
    {
      title: '更新时间',
      dataIndex: 'updatedTime',
      width: 170,
      search: false,
      render: (_, r) => fmtTime(r.updatedTime),
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      fixed: 'right',
      render: (_, r) => (
        <Space size={4} wrap>
          {can('user:edit') ? (
            <a onClick={() => void openEdit(r)}>修改</a>
          ) : null}
          {can('user:delete') ? (
            <Popconfirm
              title={`是否确认删除用户编号为${r.id}的这条数据`}
              onConfirm={() => void handleDelete(r)}
            >
              <a style={{ color: '#ff4d4f' }}>删除</a>
            </Popconfirm>
          ) : null}
          {can('user:edit') ? (
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'avatar',
                    icon: <UploadOutlined />,
                    label: '上传头像',
                    onClick: () => setAvatarUser(r),
                  },
                  {
                    key: 'password',
                    icon: <LockOutlined />,
                    label: '重置密码',
                    onClick: () => setPwdUser(r),
                  },
                  {
                    key: 'role',
                    icon: <TeamOutlined />,
                    label: '分配角色',
                    onClick: () => void openAssignRoles(r),
                  },
                ],
              }}
            >
              <Button type="link" size="small" icon={<MoreOutlined />} />
            </Dropdown>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <>
      <ProTable<UserRow>
        headerTitle="用户管理"
        rowKey="id"
        actionRef={actionRef}
        columns={columns}
        cardBordered
        search={{ labelWidth: 'auto' }}
        rowSelection={{
          selectedRowKeys,
          onChange: (keys) => setSelectedRowKeys(keys),
        }}
        tableAlertOptionRender={
          can('user:delete')
            ? () => (
                <Button danger type="text" onClick={handleBatchDelete}>
                  批量删除
                </Button>
              )
            : undefined
        }
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
        ]}
      />

      {/* 新增 / 编辑用户（编辑时不显示 password 与 isActive；username 仅展示） */}
      <Modal
        title={editing ? `修改用户` : '新增用户'}
        open={formOpen}
        confirmLoading={submitting}
        onOk={() => void handleFormSubmit()}
        onCancel={() => setFormOpen(false)}
        destroyOnHidden
        forceRender
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            postIds: [],
            isActive: true,
            gender: undefined,
          }}
        >
          <Form.Item
            name="nickname"
            label="用户昵称"
            rules={[{ required: true, message: '用户昵称为必填项' }]}
          >
            <Input placeholder="请输入用户昵称" maxLength={64} />
          </Form.Item>
          <Form.Item
            name="username"
            label="用户名称"
            rules={[
              { required: true, message: '用户名称为必填项' },
              { min: 3, max: 50, message: '长度 3-50 个字符' },
            ]}
          >
            <Input placeholder="请输入用户名称" disabled={!!editing} />
          </Form.Item>
          {!editing ? (
            <Form.Item
              name="password"
              label="用户密码"
              rules={[
                { required: true, message: '用户密码为必填项' },
                { min: 8, max: 128, message: '长度 8-128 个字符' },
              ]}
            >
              <Input.Password placeholder="请输入用户密码" />
            </Form.Item>
          ) : null}
          <Form.Item
            name="phone"
            label="手机号"
            rules={[
              {
                validator: (_rule, value: string) =>
                  !value || PHONE_PATTERN.test(value)
                    ? Promise.resolve()
                    : Promise.reject(new Error('请输入正确的手机号码格式')),
              },
            ]}
          >
            <Input placeholder="请输入手机号" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '请输入正确的邮箱格式' }]}
          >
            <Input placeholder="请输入邮箱" />
          </Form.Item>
          <Form.Item name="gender" label="用户性别">
            <Select
              allowClear
              placeholder="请选择用户性别"
              options={GENDER_OPTIONS}
            />
          </Form.Item>
          <Form.Item name="deptId" label="归属部门">
            <TreeSelect
              allowClear
              placeholder="请选择归属部门"
              treeData={toTreeSelectData(deptTree)}
              treeDefaultExpandAll
            />
          </Form.Item>
          <Form.Item name="postIds" label="归属岗位">
            <Select
              mode="multiple"
              allowClear
              placeholder="请选择归属岗位"
              options={postOptions.map((p) => ({
                label: p.postName,
                value: p.id,
              }))}
            />
          </Form.Item>
          {!editing ? (
            <Form.Item name="isActive" label="用户状态" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="停用" />
            </Form.Item>
          ) : null}
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述信息" rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配角色（对齐 Vue role.vue：用户昵称只读 + 角色多选） */}
      <Modal
        title={roleUser ? `分配 ${roleUser.username} 用户的角色` : '分配角色'}
        open={!!roleUser}
        confirmLoading={roleSaving}
        onOk={() => void handleAssignRoles()}
        onCancel={() => setRoleUser(null)}
        destroyOnHidden
        forceRender
      >
        <Form layout="vertical">
          <Form.Item label="用户昵称">
            <Input value={roleUser?.nickname ?? ''} disabled />
          </Form.Item>
          <Form.Item label="角色列表" required>
            <Select
              mode="multiple"
              allowClear
              placeholder="请选择"
              style={{ width: '100%' }}
              value={roleIds}
              onChange={(v) => setRoleIds(v)}
              options={roleOptions.map((r) => ({ label: r.name, value: r.id }))}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 重置密码 */}
      <Modal
        title={pwdUser ? `重置 ${pwdUser.username} 用户的密码` : '重置密码'}
        open={!!pwdUser}
        confirmLoading={pwdSaving}
        onOk={() => void handleResetPassword()}
        onCancel={() => {
          setPwdUser(null);
          pwdForm.resetFields();
        }}
        destroyOnHidden
        forceRender
      >
        <Form form={pwdForm} layout="vertical">
          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' },
              // 后端 ResetPasswordDTO 要求 8-128 位
              { min: 8, max: 128, message: '长度 8-128 个字符' },
            ]}
          >
            <Input.Password placeholder="请输入新密码" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 上传头像（对齐 Vue handleUpload：裁剪预览占位，确认后刷新列表） */}
      <Modal
        title="裁剪、上传头像"
        open={!!avatarUser}
        okText="确定"
        cancelText="取消"
        onOk={() => {
          setAvatarUser(null);
          actionRef.current?.reload();
        }}
        onCancel={() => setAvatarUser(null)}
        destroyOnHidden
        forceRender
      >
        <div style={{ textAlign: 'center' }}>
          <Avatar
            src={avatarUser?.avatar || DEFAULT_AVATAR}
            size={120}
            style={{ marginBottom: 12 }}
          />
        </div>
      </Modal>
    </>
  );
}
