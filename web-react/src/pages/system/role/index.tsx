/** 角色管理页：ProTable 分页列表 + 新增/编辑 Modal + 菜单授权 Drawer + 数据权限 Drawer */
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  App,
  Button,
  Drawer,
  Form,
  Input,
  Modal,
  Popconfirm,
  Radio,
  Space,
  Spin,
  Switch,
  Tag,
  Tree,
} from 'antd';
import type { DataNode } from 'antd/es/tree';
import { useRef, useState } from 'react';
import {
  createRole,
  type DeptTreeNode,
  deleteRole,
  getDeptTree,
  getMenuTree,
  getRoleMenuIds,
  getRoles,
  type MenuTreeItem,
  type RoleRow,
  saveRoleDataScope,
  saveRoleMenu,
  updateRole,
  updateRoleStatus,
} from '@/services/api';

/** 数据权限范围：1全部/2自定义/3本部门/4本部门及以下/5仅本人 */
const DATA_SCOPE_MAP: Record<number, { text: string; color: string }> = {
  1: { text: '全部', color: 'green' },
  2: { text: '自定义', color: 'orange' },
  3: { text: '本部门', color: 'blue' },
  4: { text: '本部门及以下', color: 'purple' },
  5: { text: '仅本人', color: 'red' },
};

const DATA_SCOPE_OPTIONS: Array<{ value: number; label: string }> = [
  { value: 1, label: '全部数据权限' },
  { value: 2, label: '自定义数据权限' },
  { value: 3, label: '本部门数据权限' },
  { value: 4, label: '本部门及以下数据权限' },
  { value: 5, label: '仅本人数据权限' },
];

/** 新增/编辑表单值 */
interface RoleFormValues {
  name?: string;
  code?: string;
  isActive?: boolean;
  description?: string;
}

/** 列表行附加 deptIds（后端 RoleResponseDTO 返回，仅用于数据权限回显） */
type ScopeRow = RoleRow & { deptIds?: string[] };

/** 扁平菜单列表 → antd Tree treeData */
function buildMenuTreeData(items: MenuTreeItem[]): DataNode[] {
  const map = new Map<string, DataNode>();
  items.forEach((it) => {
    map.set(it.id, { key: it.id, title: it.title || it.name, children: [] });
  });
  const roots: DataNode[] = [];
  items.forEach((it) => {
    const node = map.get(it.id);
    if (!node) return;
    const parent = it.parentId ? map.get(it.parentId) : undefined;
    if (parent) {
      (parent.children as DataNode[]).push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

/** 菜单叶子节点 id 集合（树中没有任何子节点的项） */
function menuLeafIds(items: MenuTreeItem[]): Set<string> {
  const parentIds = new Set(
    items.filter((it) => it.parentId).map((it) => it.parentId as string),
  );
  return new Set(
    items.filter((it) => !parentIds.has(it.id)).map((it) => it.id),
  );
}

/** 部门树 → antd Tree treeData */
function buildDeptTreeData(nodes: DeptTreeNode[]): DataNode[] {
  return nodes.map((n) => ({
    key: n.id,
    title: n.name,
    children:
      n.children && n.children.length > 0
        ? buildDeptTreeData(n.children)
        : undefined,
  }));
}

function errText(e: unknown): string {
  return e instanceof Error ? e.message : '操作失败';
}

export default function RolePage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const actionRef = useRef<ActionType>(null);
  const [form] = Form.useForm<RoleFormValues>();

  /** 按钮级权限码校验 */
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<RoleRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // 菜单授权 Drawer
  const [menuRole, setMenuRole] = useState<RoleRow | null>(null);
  const [menuTreeData, setMenuTreeData] = useState<DataNode[]>([]);
  const [menuCheckedKeys, setMenuCheckedKeys] = useState<React.Key[]>([]);
  const [menuHalfCheckedKeys, setMenuHalfCheckedKeys] = useState<React.Key[]>(
    [],
  );
  const [menuLoading, setMenuLoading] = useState(false);
  const [menuSaving, setMenuSaving] = useState(false);
  const menuTreeCache = useRef<MenuTreeItem[] | null>(null);

  // 数据权限 Drawer
  const [scopeRole, setScopeRole] = useState<ScopeRow | null>(null);
  const [scopeValue, setScopeValue] = useState<number>(1);
  const [scopeDeptIds, setScopeDeptIds] = useState<string[]>([]);
  const [scopeDeptTree, setScopeDeptTree] = useState<DataNode[]>([]);
  const [scopeLoading, setScopeLoading] = useState(false);
  const [scopeSaving, setScopeSaving] = useState(false);
  const deptTreeCache = useRef<DeptTreeNode[] | null>(null);

  /** 打开新增/编辑弹窗 */
  function openForm(row: RoleRow | null): void {
    setEditing(row);
    if (row) {
      form.setFieldsValue({
        name: row.name,
        code: row.code,
        isActive: row.isActive === 1,
        description: row.description ?? '',
      });
    } else {
      form.resetFields();
    }
    setFormOpen(true);
  }

  /** 提交新增/编辑表单 */
  async function handleFormSubmit(): Promise<void> {
    try {
      const values = await form.validateFields();
      setSubmitting(true);
      const payload = { ...values, isActive: values.isActive ? 1 : 0 };
      if (editing) {
        await updateRole(editing.id, payload);
        message.success('修改角色成功');
      } else {
        await createRole(payload);
        message.success('创建角色成功');
      }
      setFormOpen(false);
      actionRef.current?.reload();
    } catch (e) {
      const err = e as { errorFields?: unknown };
      if (!err?.errorFields) message.error(errText(e));
    } finally {
      setSubmitting(false);
    }
  }

  /** 删除角色 */
  async function handleDelete(id: string): Promise<void> {
    try {
      await deleteRole(id);
      message.success('删除成功');
      actionRef.current?.reload();
    } catch (e) {
      message.error(errText(e));
    }
  }

  /** 打开菜单授权 Drawer：加载菜单树 + 回显已授权菜单（叶子级联由 Tree 联动推导） */
  async function openMenuDrawer(row: RoleRow): Promise<void> {
    setMenuRole(row);
    setMenuLoading(true);
    try {
      const tree = menuTreeCache.current ?? (await getMenuTree());
      menuTreeCache.current = tree;
      setMenuTreeData(buildMenuTreeData(tree));
      const granted = await getRoleMenuIds(row.id);
      const leaves = menuLeafIds(tree);
      // 仅回显叶子：父节点勾选/半选状态由 Tree 父子联动自动推导，
      // 避免级联模式把未授权的兄弟节点污染成已授权
      setMenuCheckedKeys(granted.filter((id) => leaves.has(id)));
      setMenuHalfCheckedKeys([]);
    } catch (e) {
      message.error(errText(e));
    } finally {
      setMenuLoading(false);
    }
  }

  /** 保存菜单授权（勾选 + 半选父级一并提交，避免父目录未授权导致动态路由孤儿） */
  async function handleSaveMenu(): Promise<void> {
    if (!menuRole) return;
    try {
      setMenuSaving(true);
      const menuIds = [...menuCheckedKeys, ...menuHalfCheckedKeys].map(String);
      await saveRoleMenu(menuRole.id, menuIds);
      message.success(`角色 ${menuRole.name} 的菜单权限保存成功`);
      setMenuRole(null);
    } catch (e) {
      message.error(errText(e));
    } finally {
      setMenuSaving(false);
    }
  }

  /** 打开数据权限 Drawer：用行内 dataScope / deptIds 回显 */
  async function openScopeDrawer(row: RoleRow): Promise<void> {
    const scopeRow = row as ScopeRow;
    setScopeRole(scopeRow);
    setScopeValue(scopeRow.dataScope ?? 1);
    setScopeDeptIds(scopeRow.deptIds ?? []);
    if (!deptTreeCache.current) {
      setScopeLoading(true);
      try {
        const tree = await getDeptTree();
        deptTreeCache.current = tree;
        setScopeDeptTree(buildDeptTreeData(tree));
      } catch (e) {
        message.error(errText(e));
      } finally {
        setScopeLoading(false);
      }
    }
  }

  /** 保存数据权限 */
  async function handleSaveScope(): Promise<void> {
    if (!scopeRole) return;
    try {
      setScopeSaving(true);
      await saveRoleDataScope(scopeRole.id, {
        dataScope: scopeValue,
        deptIds: scopeValue === 2 ? scopeDeptIds : [],
      });
      message.success(`角色 ${scopeRole.name} 的数据权限保存成功`);
      setScopeRole(null);
      actionRef.current?.reload();
    } catch (e) {
      message.error(errText(e));
    } finally {
      setScopeSaving(false);
    }
  }

  const columns: ProColumns<RoleRow>[] = [
    { title: '角色名称', dataIndex: 'name', ellipsis: true },
    { title: '角色编码', dataIndex: 'code', ellipsis: true, copyable: true },
    {
      title: '数据权限',
      dataIndex: 'dataScope',
      search: false,
      width: 120,
      render: (_, r) => {
        const info = DATA_SCOPE_MAP[r.dataScope];
        return info ? <Tag color={info.color}>{info.text}</Tag> : r.dataScope;
      },
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
          disabled={!can('role:manage')}
          onChange={async (checked) => {
            try {
              await updateRoleStatus(r.id, checked ? 1 : 0);
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
      title: '描述',
      dataIndex: 'description',
      search: false,
      ellipsis: true,
      render: (_, r) => r.description ?? '-',
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
      width: 240,
      fixed: 'right',
      render: (_, r) => (
        <Space size={4} wrap>
          {can('role:manage') ? <a onClick={() => openForm(r)}>编辑</a> : null}
          {can('role:manage') ? (
            <a onClick={() => void openMenuDrawer(r)}>菜单授权</a>
          ) : null}
          {can('role:manage') ? (
            <a onClick={() => void openScopeDrawer(r)}>数据权限</a>
          ) : null}
          {can('role:manage') ? (
            <Popconfirm
              title="删除角色"
              description={`确定删除角色 ${r.name} 吗？`}
              onConfirm={() => void handleDelete(r.id)}
            >
              <a style={{ color: '#ff4d4f' }}>删除</a>
            </Popconfirm>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <>
      <ProTable<RoleRow>
        headerTitle="角色列表"
        rowKey="id"
        actionRef={actionRef}
        columns={columns}
        cardBordered
        search={{ labelWidth: 'auto' }}
        request={async (params) => {
          // 后端 POST 分页契约：pageNum/pageSize
          const { current, pageSize, ...rest } = params;
          const page = await getRoles({ ...rest, pageNum: current, pageSize });
          return { data: page.list, success: true, total: page.total };
        }}
        toolBarRender={() => [
          can('role:manage') ? (
            <Button key="create" type="primary" onClick={() => openForm(null)}>
              新增角色
            </Button>
          ) : null,
        ]}
      />

      {/* 新增 / 编辑角色 */}
      <Modal
        title={editing ? `编辑角色：${editing.name}` : '新增角色'}
        open={formOpen}
        confirmLoading={submitting}
        onOk={() => void handleFormSubmit()}
        onCancel={() => setFormOpen(false)}
        destroyOnHidden
        forceRender
      >
        <Form form={form} layout="vertical" initialValues={{ isActive: true }}>
          <Form.Item
            name="name"
            label="角色名称"
            rules={[
              { required: true, message: '请输入角色名称' },
              { min: 2, max: 64, message: '长度 2-64 个字符' },
            ]}
          >
            <Input placeholder="请输入角色名称" maxLength={64} />
          </Form.Item>
          <Form.Item
            name="code"
            label="角色编码"
            rules={[
              { required: true, message: '请输入角色编码' },
              { min: 2, max: 64, message: '长度 2-64 个字符' },
            ]}
          >
            <Input placeholder="请输入角色编码" maxLength={64} />
          </Form.Item>
          <Form.Item name="isActive" label="状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={3} maxLength={500} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 菜单授权 Drawer */}
      <Drawer
        title={menuRole ? `菜单授权：${menuRole.name}` : '菜单授权'}
        width={480}
        open={!!menuRole}
        onClose={() => setMenuRole(null)}
        destroyOnHidden
        extra={
          <Button
            type="primary"
            loading={menuSaving}
            onClick={() => void handleSaveMenu()}
          >
            保存
          </Button>
        }
      >
        {menuLoading ? (
          <Spin style={{ display: 'block', margin: '48px auto' }} />
        ) : (
          <Tree
            checkable
            defaultExpandAll
            treeData={menuTreeData}
            checkedKeys={menuCheckedKeys}
            onCheck={(checked, info) => {
              // checkStrictly=false：checked 为 Key[]（含联动勾选的父级）
              const keys = Array.isArray(checked) ? checked : checked.checked;
              setMenuCheckedKeys(keys);
              setMenuHalfCheckedKeys(info.halfCheckedKeys ?? []);
            }}
          />
        )}
      </Drawer>

      {/* 数据权限 Drawer */}
      <Drawer
        title={scopeRole ? `数据权限：${scopeRole.name}` : '数据权限'}
        width={480}
        open={!!scopeRole}
        onClose={() => setScopeRole(null)}
        destroyOnHidden
        extra={
          <Button
            type="primary"
            loading={scopeSaving}
            onClick={() => void handleSaveScope()}
          >
            保存
          </Button>
        }
      >
        {scopeLoading ? (
          <Spin style={{ display: 'block', margin: '48px auto' }} />
        ) : (
          <>
            <Radio.Group
              value={scopeValue}
              onChange={(e) => setScopeValue(e.target.value as number)}
              style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
            >
              {DATA_SCOPE_OPTIONS.map((opt) => (
                <Radio key={opt.value} value={opt.value}>
                  {opt.label}
                </Radio>
              ))}
            </Radio.Group>
            {scopeValue === 2 ? (
              <div style={{ marginTop: 16 }}>
                <div
                  style={{
                    marginBottom: 8,
                    color: 'rgba(0,0,0,0.45)',
                    fontSize: 12,
                  }}
                >
                  请勾选自定义数据权限的部门
                </div>
                <Tree
                  checkable
                  defaultExpandAll
                  treeData={scopeDeptTree}
                  checkedKeys={scopeDeptIds}
                  onCheck={(checked) => {
                    const keys = Array.isArray(checked)
                      ? checked
                      : checked.checked;
                    setScopeDeptIds(keys.map(String));
                  }}
                />
              </div>
            ) : null}
          </>
        )}
      </Drawer>
    </>
  );
}
