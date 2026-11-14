/** 菜单管理页：扁平列表客户端建树 → 树形表格（pagination=false）+ 新增/编辑/新增子菜单 Modal */
import { PlusOutlined } from '@ant-design/icons';
import type { ProColumns } from '@ant-design/pro-components';
import { ProTable } from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  App,
  Button,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Radio,
  Select,
  Space,
  Switch,
  Tag,
  TreeSelect,
} from 'antd';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  createMenu,
  deleteMenu,
  getMenuList,
  type MenuRow,
  updateMenu,
  updateMenuStatus,
} from '@/services/api';

/** TreeSelect 需要的节点结构 */
interface TreeSelectNode {
  title: string;
  value: string;
  children?: TreeSelectNode[];
}

/** 菜单类型文案 */
const MENU_TYPE_LABELS: Record<number, string> = {
  0: '目录',
  1: '页面',
  2: '按钮',
};

/** 新增/编辑表单值 */
interface MenuFormValues {
  menuType?: number;
  parentId?: string;
  name?: string;
  title?: string;
  path?: string;
  component?: string;
  method?: string;
  rank?: number;
  icon?: string;
  isActive?: boolean;
  isShowMenu?: boolean;
  isKeepalive?: boolean;
  isHiddenTag?: boolean;
}

/** 扁平菜单列表（含 parentId）→ 树形 dataSource（保持 rank 排序） */
function buildMenuTree(rows: MenuRow[]): MenuRow[] {
  const map = new Map<string, MenuRow>();
  rows.forEach((r) => {
    map.set(r.id, { ...r, children: [] });
  });
  const roots: MenuRow[] = [];
  [...map.values()]
    .sort((a, b) => a.rank - b.rank)
    .forEach((node) => {
      const parent = node.parentId ? map.get(node.parentId) : undefined;
      if (parent) {
        (parent.children as MenuRow[]).push(node);
      } else {
        roots.push(node);
      }
    });
  const sortTree = (nodes: MenuRow[]): MenuRow[] =>
    nodes
      .sort((a, b) => a.rank - b.rank)
      .map((n) => ({
        ...n,
        children:
          n.children && n.children.length > 0
            ? sortTree(n.children as MenuRow[])
            : undefined,
      }));
  return sortTree(roots);
}

/** 收集树中全部节点 id（用于默认展开全部行） */
function collectIds(nodes: MenuRow[]): string[] {
  return nodes.flatMap((n) => [
    n.id,
    ...collectIds((n.children as MenuRow[] | undefined) ?? []),
  ]);
}

/** 过滤掉指定节点及其子树（编辑时禁止把菜单挂到自身下） */
function filterNode(nodes: MenuRow[], excludeId: string | null): MenuRow[] {
  return nodes
    .filter((n) => n.id !== excludeId)
    .map((n) => ({
      ...n,
      children: n.children
        ? filterNode(n.children as MenuRow[], excludeId)
        : undefined,
    }));
}

/** 菜单树 → TreeSelect treeData（目录/页面可作上级，按钮不行） */
function toTreeSelectData(nodes: MenuRow[]): TreeSelectNode[] {
  return nodes
    .filter((n) => n.menuType !== 2)
    .map((n) => ({
      title: `${MENU_TYPE_LABELS[n.menuType] ?? ''}·${n.meta?.title || n.name}`,
      value: n.id,
      children:
        n.children && n.children.length > 0
          ? toTreeSelectData(n.children as MenuRow[])
          : undefined,
    }));
}

function errText(e: unknown): string {
  return e instanceof Error ? e.message : '操作失败';
}

export default function MenuPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;
  const [form] = Form.useForm<MenuFormValues>();

  const [flatRows, setFlatRows] = useState<MenuRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<MenuRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const dataSource = useMemo(() => buildMenuTree(flatRows), [flatRows]);
  const parentOptions = useMemo(
    () => toTreeSelectData(filterNode(dataSource, editing?.id ?? null)),
    [dataSource, editing],
  );

  /** 拉取菜单列表并默认展开全部 */
  const load = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      const rows = await getMenuList();
      setFlatRows(rows);
      setExpandedKeys(collectIds(buildMenuTree(rows)));
    } catch (e) {
      message.error(errText(e));
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    void load();
  }, [load]);

  /** 打开新增/编辑弹窗；row 为 null 表示新增顶级菜单 */
  function openForm(row: MenuRow | null): void {
    setEditing(row);
    if (row) {
      form.setFieldsValue({
        menuType: row.menuType,
        parentId: row.parentId ?? undefined,
        name: row.name,
        title: row.meta?.title,
        path: row.path,
        component: row.component ?? undefined,
        method: row.method ?? undefined,
        rank: row.rank,
        icon: row.meta?.icon,
        isActive: row.isActive === 1,
        isShowMenu: row.meta?.isShowMenu !== 0,
        isKeepalive: row.meta?.isKeepalive === 1,
        isHiddenTag: row.meta?.isHiddenTag === 1,
      });
    } else {
      form.resetFields();
    }
    setFormOpen(true);
  }

  /** 打开「新增子菜单」：预填上级菜单，类型按父节点推断 */
  function openCreateChild(row: MenuRow): void {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({
      parentId: row.id,
      // 目录下默认建页面，页面下默认建按钮
      menuType: row.menuType === 0 ? 1 : 2,
      isActive: true,
      isShowMenu: true,
    });
    setFormOpen(true);
  }

  /** 提交新增/编辑表单（DTO 为扁平结构：title/icon 在顶层） */
  async function handleFormSubmit(): Promise<void> {
    try {
      const values = await form.validateFields();
      const name = values.name;
      if (!name) {
        message.warning('请输入菜单名称');
        return;
      }
      setSubmitting(true);
      const payload = {
        menuType: values.menuType ?? 0,
        parentId: values.parentId ?? null,
        name,
        title: values.title,
        path: values.path,
        component: values.component,
        method: values.method,
        rank: values.rank ?? 0,
        icon: values.icon,
        isActive: values.isActive === false ? 0 : 1,
        isShowMenu: values.isShowMenu === false ? 0 : 1,
        isKeepalive: values.isKeepalive === true ? 1 : 0,
        isHiddenTag: values.isHiddenTag === true ? 1 : 0,
      };
      if (editing) {
        await updateMenu(editing.id, payload);
        message.success('修改菜单成功');
      } else {
        await createMenu(payload);
        message.success('创建菜单成功');
      }
      setFormOpen(false);
      await load();
    } catch (e) {
      // 表单校验失败（带 errorFields）不弹错误提示
      const err = e as { errorFields?: unknown };
      if (!err?.errorFields) message.error(errText(e));
    } finally {
      setSubmitting(false);
    }
  }

  /** 删除菜单 */
  async function handleDelete(id: string): Promise<void> {
    try {
      await deleteMenu(id);
      message.success('删除成功');
      await load();
    } catch (e) {
      message.error(errText(e));
    }
  }

  const columns: ProColumns<MenuRow>[] = [
    { title: '菜单名称', dataIndex: 'name', ellipsis: true },
    {
      title: '类型',
      dataIndex: 'menuType',
      width: 80,
      align: 'center',
      render: (_, r) => <Tag>{MENU_TYPE_LABELS[r.menuType] ?? r.menuType}</Tag>,
    },
    {
      title: '路由路径',
      dataIndex: 'path',
      width: 160,
      ellipsis: true,
      render: (_, r) => r.path ?? '-',
    },
    {
      title: '组件路径',
      dataIndex: 'component',
      width: 180,
      ellipsis: true,
      render: (_, r) => r.component ?? '-',
    },
    {
      title: '显示',
      dataIndex: 'isShowMenu',
      width: 80,
      align: 'center',
      render: (_, r) =>
        r.meta?.isShowMenu === 0 ? (
          <Tag color="orange">隐藏</Tag>
        ) : (
          <Tag color="green">显示</Tag>
        ),
    },
    { title: '排序', dataIndex: 'rank', width: 70, align: 'center' },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      render: (_, r) => (
        <Switch
          checked={r.isActive === 1}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          disabled={!can('menu:edit')}
          onChange={async (checked) => {
            try {
              await updateMenuStatus(r.id, checked ? 1 : 0);
              message.success('状态更新成功');
              await load();
            } catch (e) {
              message.error(errText(e));
            }
          }}
        />
      ),
    },
    {
      title: '操作',
      valueType: 'option',
      width: 200,
      render: (_, r) =>
        can('menu:edit') || can('menu:add') || can('menu:delete')
          ? [
              can('menu:add') && (
                <a key="addChild" onClick={() => openCreateChild(r)}>
                  新增子项
                </a>
              ),
              can('menu:edit') && (
                <a key="edit" onClick={() => openForm(r)}>
                  编辑
                </a>
              ),
              can('menu:delete') && (
                <Popconfirm
                  key="del"
                  title="确认删除该菜单？"
                  onConfirm={() => handleDelete(r.id)}
                >
                  <a style={{ color: '#ff4d4f' }}>删除</a>
                </Popconfirm>
              ),
            ].filter(Boolean)
          : [],
    },
  ];

  return (
    <>
      <ProTable<MenuRow>
        headerTitle="菜单管理"
        rowKey="id"
        search={false}
        pagination={false}
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        expandable={{
          expandedRowKeys: expandedKeys,
          onExpandedRowsChange: (keys) => setExpandedKeys([...keys]),
        }}
        options={false}
        toolBarRender={() => [
          can('menu:add') ? (
            <Button
              key="add"
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => openForm(null)}
            >
              新增菜单
            </Button>
          ) : null,
        ]}
      />

      <Modal
        title={
          editing
            ? `编辑菜单：${editing.meta?.title || editing.name}`
            : '新增菜单'
        }
        open={formOpen}
        width={640}
        onCancel={() => setFormOpen(false)}
        onOk={handleFormSubmit}
        confirmLoading={submitting}
        destroyOnHidden
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            menuType: 0,
            rank: 0,
            isActive: true,
            isShowMenu: true,
          }}
        >
          <Form.Item
            name="menuType"
            label="菜单类型"
            rules={[{ required: true }]}
          >
            <Radio.Group disabled={!!editing}>
              <Radio value={0}>目录</Radio>
              <Radio value={1}>页面</Radio>
              <Radio value={2}>按钮</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item name="parentId" label="上级菜单">
            <TreeSelect
              treeData={parentOptions}
              treeDefaultExpandAll
              allowClear
              placeholder="不选则为顶级"
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="名称（权限码）"
            rules={[
              { required: true, message: '请输入菜单名称' },
              { max: 128 },
            ]}
          >
            <Input placeholder="如 user:add（按钮权限码）或路由名" />
          </Form.Item>
          <Form.Item name="title" label="显示标题">
            <Input maxLength={255} placeholder="菜单显示名称" />
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.menuType !== cur.menuType}
          >
            {({ getFieldValue }) =>
              getFieldValue('menuType') !== 2 ? (
                <Form.Item name="path" label="路由路径">
                  <Input maxLength={255} placeholder="如 /system/user" />
                </Form.Item>
              ) : (
                <Form.Item name="method" label="HTTP 方法">
                  <Select
                    allowClear
                    placeholder="用于 API 权限校验"
                    options={['GET', 'POST', 'PUT', 'DELETE'].map((m) => ({
                      value: m,
                      label: m,
                    }))}
                  />
                </Form.Item>
              )
            }
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(prev, cur) => prev.menuType !== cur.menuType}
          >
            {({ getFieldValue }) =>
              getFieldValue('menuType') === 1 ? (
                <Form.Item name="component" label="组件路径">
                  <Input maxLength={255} placeholder="如 system/user/index" />
                </Form.Item>
              ) : null
            }
          </Form.Item>
          <Form.Item name="rank" label="排序号">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="icon" label="图标（iconify 名）">
            <Input
              maxLength={255}
              placeholder="如 ri:table-line / ep:setting"
            />
          </Form.Item>
          <Space size={24} wrap>
            <Form.Item name="isActive" label="状态" valuePropName="checked">
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
            <Form.Item
              name="isShowMenu"
              label="菜单中显示"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="isKeepalive"
              label="页面缓存"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="isHiddenTag"
              label="隐藏标签页"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </>
  );
}
