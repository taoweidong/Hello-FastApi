/** 部门管理页：树形表格（pagination=false）+ 名称/状态搜索 + 新增/编辑/新增子部门 Modal（对齐 Vue useDept） */
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
  Select,
  Space,
  Switch,
  Tag,
  TreeSelect,
} from 'antd';
import dayjs from 'dayjs';
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

/** 搜索表单值（对齐 Vue form: { name, isActive }） */
interface DeptSearchValues {
  name?: string;
  isActive?: number;
}

/** 时间格式化（对齐 Vue dayjs YYYY-MM-DD HH:mm:ss） */
function fmtTime(v: string | null | undefined): string {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-';
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
  const [searchForm] = Form.useForm<DeptSearchValues>();

  /** 按钮级权限码校验 */
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;

  const [flatRows, setFlatRows] = useState<DeptRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  /** 已应用的搜索条件（点击搜索后才生效，对齐 Vue onSearch 行为） */
  const [filters, setFilters] = useState<DeptSearchValues>({});

  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<DeptRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  /** 搜索过滤（名称包含 + 状态相等，客户端过滤对齐 Vue onSearch） */
  const filteredRows = useMemo(
    () =>
      flatRows.filter(
        (r) =>
          (!filters.name || r.name.includes(filters.name)) &&
          (filters.isActive === undefined ||
            filters.isActive === null ||
            r.isActive === filters.isActive),
      ),
    [flatRows, filters],
  );

  const dataSource = useMemo(() => buildDeptTree(filteredRows), [filteredRows]);
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

  /** 搜索（对齐 Vue onSearch：本地过滤后重建树） */
  function handleSearch(v: DeptSearchValues): void {
    setFilters({ name: v.name, isActive: v.isActive });
  }

  /** 重置搜索（对齐 Vue resetForm：清空后重新加载） */
  function handleSearchReset(): void {
    searchForm.resetFields();
    setFilters({});
  }

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
        description: values.description || null,
      };
      if (editing) {
        await updateDept(editing.id, payload);
        message.success(`成功更新部门 ${name}`);
      } else {
        // sys_departments.code 唯一非空，后端不自动生成；
        // 不生成唯一编码会与历史空编码行冲突触发 500（对齐 Vue 的处理）
        await createDept({
          ...payload,
          code: `DEPT_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        });
        message.success(`成功创建部门 ${name}`);
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
  async function handleDelete(row: DeptRow): Promise<void> {
    try {
      await deleteDept(row.id);
      message.success(`已成功删除部门 ${row.name}`);
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
        <Tag color={r.isActive === 1 ? 'success' : 'default'}>
          {r.isActive === 1 ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'createdTime',
      width: 170,
      render: (_, r) => fmtTime(r.createdTime),
    },
    {
      title: '更新时间',
      dataIndex: 'updatedTime',
      width: 170,
      render: (_, r) => fmtTime(r.updatedTime),
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
          {can('dept:edit') ? <a onClick={() => openForm(r)}>修改</a> : null}
          {can('dept:delete') ? (
            <Popconfirm
              title={`是否确认删除部门名称为${r.name}的这条数据`}
              onConfirm={() => void handleDelete(r)}
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
      {/* 搜索表单（对齐 Vue：部门名称 / 状态，客户端过滤） */}
      <Form
        form={searchForm}
        layout="inline"
        onFinish={handleSearch}
        style={{ marginBottom: 16, rowGap: 8 }}
      >
        <Form.Item name="name" label="部门名称">
          <Input
            placeholder="请输入部门名称"
            allowClear
            style={{ width: 180 }}
          />
        </Form.Item>
        <Form.Item name="isActive" label="状态">
          <Select
            placeholder="请选择状态"
            allowClear
            style={{ width: 140 }}
            options={[
              { label: '启用', value: 1 },
              { label: '停用', value: 0 },
            ]}
          />
        </Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={loading}>
              搜索
            </Button>
            <Button onClick={handleSearchReset}>重置</Button>
          </Space>
        </Form.Item>
      </Form>

      <div>
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
      </div>
      {/* 树形表格：不分页，dataSource 按 parentId 组装 */}
      <ProTable<DeptRow>
        headerTitle="部门管理"
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
        title={editing ? `修改部门` : '新增部门'}
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
          <Form.Item name="parentId" label="上级部门">
            <TreeSelect
              allowClear
              placeholder="不选择则为顶级部门"
              treeData={parentOptions}
              treeDefaultExpandAll
            />
          </Form.Item>
          <Form.Item
            name="name"
            label="部门名称"
            rules={[{ required: true, message: '部门名称为必填项' }]}
          >
            <Input placeholder="请输入部门名称" maxLength={64} />
          </Form.Item>
          <Form.Item name="rank" label="排序">
            <InputNumber
              min={0}
              max={9999}
              precision={0}
              style={{ width: '100%' }}
              placeholder="数值越小越靠前"
            />
          </Form.Item>
          <Form.Item name="isActive" label="部门状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea
              placeholder="请输入描述信息"
              rows={3}
              maxLength={500}
            />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
}
