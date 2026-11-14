/** 部门管理页：树形表格（pagination=false）+ 新增/编辑/新增子部门 Modal */
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
  Space,
  Switch,
  TreeSelect,
} from 'antd';
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  createDept,
  type DeptRow,
  deleteDept,
  getDeptList,
  updateDept,
} from '@/services/api';

/** TreeSelect 需要的节点结构 */
interface TreeSelectNode {
  title: string;
  value: string;
  children?: TreeSelectNode[];
}

/** 新增/编辑表单值 */
interface DeptFormValues {
  name?: string;
  parentId?: string;
  rank?: number;
  isActive?: boolean;
  description?: string;
}

/** 扁平部门列表（含 parentId）→ 树形 dataSource */
function buildDeptTree(rows: DeptRow[]): DeptRow[] {
  const map = new Map<string, DeptRow>();
  rows.forEach((r) => {
    map.set(r.id, { ...r, children: [] });
  });
  const roots: DeptRow[] = [];
  rows.forEach((r) => {
    const node = map.get(r.id);
    if (!node) return;
    const parent = r.parentId ? map.get(r.parentId) : undefined;
    if (parent) {
      (parent.children as DeptRow[]).push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

/** 收集树中全部节点 id（用于默认展开全部行） */
function collectIds(nodes: DeptRow[]): string[] {
  return nodes.flatMap((n) => [
    n.id,
    ...collectIds((n.children as DeptRow[] | undefined) ?? []),
  ]);
}

/** 过滤掉指定节点及其子树（编辑时禁止把部门挂到自身下） */
function filterNode(nodes: DeptRow[], excludeId: string | null): DeptRow[] {
  return nodes
    .filter((n) => n.id !== excludeId)
    .map((n) => ({
      ...n,
      children: n.children
        ? filterNode(n.children as DeptRow[], excludeId)
        : undefined,
    }));
}

/** 部门树 → TreeSelect treeData */
function toTreeSelectData(nodes: DeptRow[]): TreeSelectNode[] {
  return nodes.map((n) => ({
    title: n.name,
    value: n.id,
    children:
      n.children && n.children.length > 0
        ? toTreeSelectData(n.children as DeptRow[])
        : undefined,
  }));
}

function errText(e: unknown): string {
  return e instanceof Error ? e.message : '操作失败';
}

export default function DeptPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const [form] = Form.useForm<DeptFormValues>();

  /** 按钮级权限码校验 */
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;

  const [flatRows, setFlatRows] = useState<DeptRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<DeptRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const dataSource = useMemo(() => buildDeptTree(flatRows), [flatRows]);
  const parentOptions = useMemo(
    () => toTreeSelectData(filterNode(dataSource, editing?.id ?? null)),
    [dataSource, editing],
  );

  /** 拉取部门列表并默认展开全部 */
  const load = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      const rows = await getDeptList();
      setFlatRows(rows);
      setExpandedKeys(collectIds(buildDeptTree(rows)));
    } catch (e) {
      message.error(errText(e));
    } finally {
      setLoading(false);
    }
  }, [message]);

  useEffect(() => {
    void load();
  }, [load]);

  /** 打开新增/编辑弹窗；row 为 null 表示新增顶级部门 */
  function openForm(row: DeptRow | null): void {
    setEditing(row);
    if (row) {
      form.setFieldsValue({
        name: row.name,
        parentId: row.parentId ?? undefined,
        rank: row.rank,
        isActive: row.isActive === 1,
        description: row.description ?? '',
      });
    } else {
      form.resetFields();
    }
    setFormOpen(true);
  }

  /** 打开「新增子部门」：预填上级部门 */
  function openCreateChild(row: DeptRow): void {
    setEditing(null);
    form.resetFields();
    form.setFieldsValue({ parentId: row.id, isActive: true });
    setFormOpen(true);
  }

  /** 提交新增/编辑表单 */
  async function handleFormSubmit(): Promise<void> {
    try {
      const values = await form.validateFields();
      const name = values.name;
      if (!name) {
        message.warning('请输入部门名称');
        return;
      }
      setSubmitting(true);
      const payload = {
        name,
        parentId: values.parentId ?? null,
        rank: values.rank,
        isActive: values.isActive === false ? 0 : 1,
        description: values.description,
      };
      if (editing) {
        await updateDept(editing.id, payload);
        message.success('修改部门成功');
      } else {
        await createDept(payload);
        message.success('创建部门成功');
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

  /** 删除部门 */
  async function handleDelete(id: string): Promise<void> {
    try {
      await deleteDept(id);
      message.success('删除成功');
      await load();
    } catch (e) {
      message.error(errText(e));
    }
  }

  const columns: ProColumns<DeptRow>[] = [
    { title: '部门名称', dataIndex: 'name', ellipsis: true },
    {
      title: '部门编码',
      dataIndex: 'code',
      ellipsis: true,
      render: (_, r) => r.code ?? '-',
    },
    { title: '排序', dataIndex: 'rank', width: 80, align: 'center' },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      render: (_, r) => (
        <Switch
          checked={r.isActive === 1}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          onChange={async (checked) => {
            try {
              // DeptPayload 的 name 必填，状态切换时原样带回
              await updateDept(r.id, {
                name: r.name,
                isActive: checked ? 1 : 0,
              });
              message.success('状态更新成功');
              await load();
            } catch (e) {
              message.error(errText(e));
            }
          }}
          disabled={!can('dept:edit')}
        />
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      ellipsis: true,
      render: (_, r) => r.description ?? '-',
    },
    {
      title: '操作',
      valueType: 'option',
      width: 220,
      render: (_, r) => (
        <Space size={4} wrap>
          {can('dept:add') ? (
            <a onClick={() => openCreateChild(r)}>新增子部门</a>
          ) : null}
          {can('dept:edit') ? <a onClick={() => openForm(r)}>编辑</a> : null}
          {can('dept:delete') ? (
            <Popconfirm
              title="删除部门"
              description={`确定删除部门 ${r.name} 吗？`}
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
      {can('dept:add') ? (
        <Button
          type="primary"
          icon={<PlusOutlined />}
          style={{ marginBottom: 16 }}
          onClick={() => openForm(null)}
        >
          新增部门
        </Button>
      ) : null}
      {/* 树形表格：不分页，dataSource 按 parentId 组装 */}
      <ProTable<DeptRow>
        headerTitle="部门列表"
        rowKey="id"
        columns={columns}
        dataSource={dataSource}
        loading={loading}
        search={false}
        pagination={false}
        options={false}
        cardBordered
        expandable={{
          expandedRowKeys: expandedKeys,
          onExpandedRowsChange: (keys) => setExpandedKeys([...keys]),
        }}
      />

      {/* 新增 / 编辑部门 */}
      <Modal
        title={editing ? `编辑部门：${editing.name}` : '新增部门'}
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
          initialValues={{ isActive: true, rank: 0 }}
        >
          <Form.Item
            name="name"
            label="部门名称"
            rules={[{ required: true, message: '请输入部门名称' }]}
          >
            <Input placeholder="请输入部门名称" maxLength={64} />
          </Form.Item>
          <Form.Item name="parentId" label="上级部门">
            <TreeSelect
              allowClear
              placeholder="不选择则为顶级部门"
              treeData={parentOptions}
              treeDefaultExpandAll
            />
          </Form.Item>
          <Form.Item name="rank" label="排序">
            <InputNumber
              min={0}
              precision={0}
              style={{ width: '100%' }}
              placeholder="数值越小越靠前"
            />
          </Form.Item>
          <Form.Item name="isActive" label="状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述" rows={3} maxLength={500} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
