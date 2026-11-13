import { useMemo, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  App,
  Button,
  Form,
  Input,
  Modal,
  Popconfirm,
  Radio,
  Select,
  Space,
  Switch,
  Tag,
  TreeSelect
} from "antd";
import { PlusOutlined } from "@ant-design/icons";
import { ProTable, type ProColumns, type ActionType } from "@ant-design/pro-components";
import {
  batchDeleteUsers,
  createUser,
  deleteUser,
  getAllRoles,
  getDeptTree,
  getPostOptions,
  getUsers,
  getUsers as _getUsers,
  updateUser,
  updateUserStatus,
  type DeptNode,
  type UserRow
} from "@/api/user";
import { hasAuth } from "@/components/icons";
import { useAuthStore } from "@/store/auth";
import { request } from "@/api/client";

/**
 * 用户管理（React 版 CRUD 参考实现）：
 * ProTable（POST /user 分页）+ 新增/编辑 ModalForm + 状态开关 + 分配角色 +
 * 批量删除；按钮按后端下发的权限码（permissions）显隐，后端二次校验。
 */

interface RoleOption {
  id: string;
  name: string;
}

interface PostOption {
  id: string;
  postName: string;
}

function toTreeSelectData(nodes: import("@/api/user").DeptNode[]): import("antd").TreeSelectProps['treeData'] {
  return nodes.map(n => ({ value: n.id, title: n.name, children: n.children ? toTreeSelectData(n.children) : undefined }));
}

export default function UserPage(): React.ReactNode {
  const actionRef = useRef<ActionType>(null);
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const permissions = useAuthStore(s => s.permissions);
  const can = (code: string) => hasAuth(permissions, code);

  // 部门树 / 角色 / 岗位 下拉数据
  const deptTree = useQuery({ queryKey: ["dept-tree"], queryFn: getDeptTree, staleTime: 5 * 60_000 });
  const roles = useQuery({ queryKey: ["all-roles"], queryFn: getAllRoles, staleTime: 5 * 60_000 });
  const posts = useQuery({ queryKey: ["post-options"], queryFn: getPostOptions, staleTime: 5 * 60_000 });

  const deptIdToName = useMemo(() => {
    const map = new Map<string, string>();
    const walk = (nodes: DeptNode[]): void => nodes.forEach(n => (map.set(n.id, n.name), walk(n.children ?? [])));
    walk(deptTree.data ?? []);
    return map;
  }, [deptTree.data]);

  // 新增 / 编辑 / 分配角色 对话框
  const [editOpen, setEditOpen] = useState(false);
  const [editing, setEditing] = useState<UserRow | null>(null);
  const [editSaving, setEditSaving] = useState(false);
  const [editForm] = Form.useForm();

  const [roleOpen, setRoleOpen] = useState(false);
  const [roleUser, setRoleUser] = useState<UserRow | null>(null);
  const [roleIds, setRoleIds] = useState<string[]>([]);
  const [roleSaving, setRoleSaving] = useState(false);

  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  function openCreate(): void {
    setEditing(null);
    editForm.resetFields();
    editForm.setFieldsValue({ isActive: 1 });
    setEditOpen(true);
  }

  function openEdit(row: UserRow): void {
    setEditing(row);
    editForm.setFieldsValue({
      username: row.username,
      nickname: row.nickname,
      email: row.email,
      phone: row.phone,
      deptId: row.dept?.id || undefined,
      isActive: row.isActive
    });
    setEditOpen(true);
  }

  async function submitEdit(): Promise<void> {
    const values = await editForm.validateFields();
    setEditSaving(true);
    try {
      if (editing) {
        await updateUser(editing.id, values);
        message.success("更新成功");
      } else {
        await createUser(values);
        message.success("创建成功");
      }
      setEditOpen(false);
      actionRef.current?.reload();
    } finally {
      setEditSaving(false);
    }
  }

  function openAssignRoles(row: UserRow): void {
    setRoleUser(row);
    setRoleIds(row.roles.map(r => r.id));
    setRoleOpen(true);
  }

  async function submitRoles(): Promise<void> {
    if (!roleUser) return;
    setRoleSaving(true);
    try {
      const { assignRoles } = await import("@/api/user");
      await assignRoles(roleUser.id, roleIds);
      message.success("角色分配成功");
      setRoleOpen(false);
      actionRef.current?.reload();
    } finally {
      setRoleSaving(false);
    }
  }

  async function handleStatus(row: UserRow, checked: boolean): Promise<void> {
    try {
      await updateUserStatus(row.id, checked ? 1 : 0);
      message.success(`已${checked ? "启用" : "停用"}用户 ${row.username}`);
      actionRef.current?.reload();
    } catch {
      message.error("状态更新失败");
    }
  }

  async function handleDelete(row: UserRow): Promise<void> {
    await deleteUser(row.id);
    message.success(`已删除用户 ${row.username}`);
    actionRef.current?.reload();
  }

  async function handleBatchDelete(ids: string[]): Promise<void> {
    const deleted = await batchDeleteUsers(ids);
    message.success(`已删除 ${deleted} 个用户`);
    setSelectedIds([]);
    actionRef.current?.reload();
  }

  const columns: ProColumns<UserRow>[] = [
    { title: "用户名", dataIndex: "username", width: 120 },
    { title: "昵称", dataIndex: "nickname", width: 120 },
    {
      title: "角色",
      dataIndex: "roles",
      width: 160,
      render: (_, row) => row.roles?.map((r: { id: string; name: string }) => <Tag key={r.id}>{r.name}</Tag>) ?? "-"
    },
    { title: "部门", dataIndex: ["dept", "name"], width: 120, render: (_, row) => row.dept?.name || "-" },
    { title: "邮箱", dataIndex: "email", width: 180 },
    {
      title: "状态",
      dataIndex: "isActive",
      width: 90,
      render: (_, row) => (
        <Switch
          checked={row.isActive === 1}
          disabled={!can("user:edit")}
          onChange={checked => handleStatus(row, checked)}
        />
      )
    },
    { title: "创建时间", dataIndex: "createdTime", width: 170 }
  ];

  return (
    <>
      <ProTable<UserRow>
        headerTitle="用户管理"
        rowKey="id"
        actionRef={actionRef}
        search={{ labelWidth: "auto" }}
        columns={[
          ...columns,
          {
            title: "操作",
            valueType: "option",
            width: 200,
            fixed: "right",
            render: (_, row) => [
              can("user:edit") && (
                <a key="edit" onClick={() => openEdit(row)}>
                  编辑
                </a>
              ),
              can("user:edit") && (
                <a key="role" onClick={() => openAssignRoles(row)}>
                  分配角色
                </a>
              ),
              can("user:delete") && (
                <Popconfirm key="del" title={`确认删除用户 ${row.username}？`} onConfirm={() => handleDelete(row)}>
                  <a style={{ color: "#ff4d4f" }}>删除</a>
                </Popconfirm>
              )
            ].filter(Boolean)
          }
        ]}
        request={async (params, _sort, _filter) => {
          const { current, pageSize, username, isActive } = params as Record<string, string | number | undefined>;
          const page = await request<{ list: UserRow[]; total: number }>({
            method: "post",
            url: "/user",
            data: {
              pageNum: current,
              pageSize,
              username: username || undefined,
              isActive: typeof isActive === "number" ? isActive : undefined
            }
          });
          return { data: page.list, success: true, total: page.total };
        }}
        rowSelection={{
          onChange: keys => setSelectedIds(keys as string[])
        }}
        toolBarRender={() => [
          can("user:add") && (
            <Button key="add" type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              新增用户
            </Button>
          ),
          can("user:delete") &&
            selectedIds.length > 0 && (
              <Popconfirm
                key="batch-del"
                title={`确认删除选中的 ${selectedIds.length} 个用户？`}
                onConfirm={() => handleBatchDelete(selectedIds)}
              >
                <Button danger>批量删除（{selectedIds.length}）</Button>
              </Popconfirm>
            )
        ].filter(Boolean)}
      />

      {/* 新增 / 编辑用户 */}
      <Modal
        title={editing ? `编辑用户：${editing.username}` : "新增用户"}
        open={editOpen}
        onCancel={() => setEditOpen(false)}
        onOk={submitEdit}
        confirmLoading={editSaving}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true, min: 3, max: 50 }]}>
            <Input disabled={!!editing} placeholder="3-50 位字母数字下划线" />
          </Form.Item>
          {!editing && (
            <Form.Item name="password" label="初始密码" rules={[{ required: true, min: 8 }]}>
              <Input.Password placeholder="≥8 位" />
            </Form.Item>
          )}
          <Form.Item name="nickname" label="昵称">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="邮箱" rules={[{ type: "email", message: "邮箱格式不正确" }]}>
            <Input />
          </Form.Item>
          <Form.Item name="phone" label="手机号">
            <Input />
          </Form.Item>
          <Form.Item name="deptId" label="部门">
            <TreeSelect
              treeData={toTreeSelectData(deptTree.data ?? [])}
              treeDefaultExpandAll
              allowClear
              placeholder="选择部门"
            />
          </Form.Item>
          {!editing && (
            <Form.Item name="postIds" label="岗位">
              <Select mode="multiple" allowClear options={(posts.data ?? []).map(p => ({ value: p.id, label: p.postName }))} />
            </Form.Item>
          )}
          <Form.Item name="isActive" label="状态">
            <Radio.Group>
              <Radio value={1}>启用</Radio>
              <Radio value={0}>停用</Radio>
            </Radio.Group>
          </Form.Item>
        </Form>
      </Modal>

      {/* 分配角色 */}
      <Modal
        title={`分配角色：${roleUser?.username ?? ""}`}
        open={roleOpen}
        onCancel={() => setRoleOpen(false)}
        onOk={submitRoles}
        confirmLoading={roleSaving}
        destroyOnClose
      >
        <Form layout="vertical">
          <Form.Item label="角色">
            <Select
              mode="multiple"
              style={{ width: "100%" }}
              value={roleIds}
              onChange={setRoleIds}
              options={(roles.data ?? []).map((r: RoleOption) => ({ value: r.id, label: r.name }))}
              placeholder="选择角色（可多选）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}

// 保留 useQueryClient 引用面（未来页面级失效使用）
void useQueryClient;
