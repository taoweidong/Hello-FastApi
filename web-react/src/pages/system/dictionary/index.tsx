/** 字典管理页面：左侧字典类型树 + 右侧字典项列表 */
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons';
import {
  type ActionType,
  type ProColumns,
  ProTable,
} from '@ant-design/pro-components';
import { useModel } from '@umijs/max';
import {
  App,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Spin,
  Switch,
  Tag,
  Tree,
} from 'antd';
import { useEffect, useRef, useState } from 'react';
import {
  createDict,
  type DictPayload,
  type DictRow,
  deleteDict,
  getDictItemsByName,
  getDictionaries,
  updateDict,
} from '@/services/api';

/** antd Tree 节点（挂原始字典行，便于 onSelect 后取回数据） */
interface DictTreeNode {
  key: string;
  title: React.ReactNode;
  children?: DictTreeNode[];
  row: DictRow;
}

/** 字典表单值（isActive 由 Switch 提供，为 boolean） */
interface DictFormValues {
  name: string;
  label?: string;
  value?: string;
  sort?: number;
  isActive: boolean;
}

type DictModalMode = 'createType' | 'createItem' | 'edit';

/** 扁平字典列表 → 树结构（parentId 为空视为根节点，即字典类型） */
function buildDictTree(rows: DictRow[]): DictRow[] {
  const nodeMap = new Map<string, DictRow>();
  for (const row of rows) nodeMap.set(row.id, { ...row });
  const roots: DictRow[] = [];
  for (const node of nodeMap.values()) {
    const parent = node.parentId ? nodeMap.get(node.parentId) : undefined;
    if (parent) {
      parent.children = parent.children ? [...parent.children, node] : [node];
    } else {
      roots.push(node);
    }
  }
  return roots;
}

/** 收集所有含子节点的节点 id（用于默认展开树） */
function collectParentIds(rows: DictRow[], acc: string[] = []): string[] {
  for (const row of rows) {
    if (row.children?.length) {
      acc.push(row.id);
      collectParentIds(row.children, acc);
    }
  }
  return acc;
}

export default function DictionaryPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  // 按钮级权限：超管直接放行（与 access.ts 的 isAdmin 口径一致），普通用户按权限码判断
  const can = (code: string): boolean =>
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes(code) ?? false);

  const actionRef = useRef<ActionType | undefined>(undefined);
  const selectedRef = useRef<DictRow | null>(null);
  const [form] = Form.useForm<DictFormValues>();

  const [flatList, setFlatList] = useState<DictRow[]>([]);
  const [treeLoading, setTreeLoading] = useState(false);
  const [selectedRow, setSelectedRow] = useState<DictRow | null>(null);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<DictModalMode>('createType');
  const [editingRow, setEditingRow] = useState<DictRow | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function applySelected(row: DictRow | null): void {
    selectedRef.current = row;
    setSelectedRow(row);
  }

  /** 拉取扁平字典列表并重建树；保持原选中项，无选中时自动选中第一个字典类型 */
  async function loadTree(): Promise<void> {
    setTreeLoading(true);
    try {
      const rows = await getDictionaries();
      setFlatList(rows);
      const prevId = selectedRef.current?.id;
      const next = prevId
        ? (rows.find((r) => r.id === prevId) ?? null)
        : (buildDictTree(rows)[0] ?? null);
      applySelected(next);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载字典失败');
    } finally {
      setTreeLoading(false);
    }
  }

  useEffect(() => {
    void loadTree();
  }, []);

  // 树数据变化后默认展开所有含子节点的层级
  useEffect(() => {
    setExpandedKeys(collectParentIds(buildDictTree(flatList)));
  }, [flatList]);

  function openCreateTypeModal(): void {
    setModalMode('createType');
    setEditingRow(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openCreateItemModal(): void {
    setModalMode('createItem');
    setEditingRow(null);
    form.resetFields();
    setModalOpen(true);
  }

  function openEditModal(row: DictRow): void {
    setModalMode('edit');
    setEditingRow(row);
    form.setFieldsValue({
      name: row.name,
      label: row.label,
      value: row.value,
      sort: row.sort,
      isActive: row.isActive === 1,
    });
    setModalOpen(true);
  }

  async function handleDeleteDict(row: DictRow): Promise<void> {
    try {
      await deleteDict(row.id);
      message.success('删除成功');
      await loadTree();
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除失败');
    }
  }

  async function handleSubmit(): Promise<void> {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSubmitting(true);
    try {
      const payload: DictPayload = {
        name: values.name,
        label: values.label,
        value: values.value,
        sort: values.sort,
        isActive: values.isActive ? 1 : 0,
      };
      if (modalMode === 'edit' && editingRow) {
        // 后端更新时缺省 parentId 会被置空，必须显式回传
        await updateDict(editingRow.id, {
          ...payload,
          parentId: editingRow.parentId,
        });
        message.success('更新成功');
      } else if (modalMode === 'createItem' && selectedRow) {
        await createDict({ ...payload, parentId: selectedRow.id });
        message.success('创建成功');
      } else {
        await createDict(payload);
        message.success('创建成功');
      }
      setModalOpen(false);
      await loadTree();
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '操作失败');
    } finally {
      setSubmitting(false);
    }
  }

  function renderTreeNodeTitle(node: DictRow): React.ReactNode {
    const actions: React.ReactNode[] = [];
    if (can('dictionary:edit')) {
      actions.push(
        <Button
          key="edit"
          type="text"
          size="small"
          icon={<EditOutlined />}
          onClick={() => openEditModal(node)}
        />,
      );
    }
    if (can('dictionary:delete')) {
      actions.push(
        <Popconfirm
          key="delete"
          title={`确定删除字典【${node.label || node.name}】吗？`}
          onConfirm={() => handleDeleteDict(node)}
        >
          <Button type="text" size="small" danger icon={<DeleteOutlined />} />
        </Popconfirm>,
      );
    }
    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
        <span>{node.label || node.name}</span>
        {node.label ? (
          <span style={{ color: 'rgba(0, 0, 0, 0.45)', fontSize: 12 }}>
            {node.name}
          </span>
        ) : null}
        {actions.length > 0 ? (
          <span onClick={(e) => e.stopPropagation()}>{actions}</span>
        ) : null}
      </span>
    );
  }

  function toTreeData(rows: DictRow[]): DictTreeNode[] {
    return rows.map((row) => ({
      key: row.id,
      row,
      title: renderTreeNodeTitle(row),
      children: row.children?.length ? toTreeData(row.children) : undefined,
    }));
  }

  const treeData = toTreeData(buildDictTree(flatList));

  const itemColumns: ProColumns<DictRow>[] = [
    { title: '标签', dataIndex: 'label', ellipsis: true },
    { title: '键值', dataIndex: 'value', ellipsis: true },
    { title: '排序', dataIndex: 'sort', width: 80 },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      render: (_, record) => (
        <Tag color={record.isActive === 1 ? 'success' : 'default'}>
          {record.isActive === 1 ? '启用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      valueType: 'option',
      width: 120,
      render: (_, record) => [
        can('dictionary:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            编辑
          </a>
        ) : null,
        can('dictionary:delete') ? (
          <Popconfirm
            key="delete"
            title={`确定删除字典项【${record.label || record.name}】吗？`}
            onConfirm={() => handleDeleteDict(record)}
          >
            <a style={{ color: '#ff4d4f' }}>删除</a>
          </Popconfirm>
        ) : null,
      ],
    },
  ];

  return (
    <Row gutter={16}>
      <Col span={8}>
        <Card
          title="字典类型"
          size="small"
          extra={
            can('dictionary:add') ? (
              <Button
                type="primary"
                size="small"
                icon={<PlusOutlined />}
                onClick={openCreateTypeModal}
              >
                新增字典类型
              </Button>
            ) : null
          }
        >
          <Spin spinning={treeLoading}>
            {treeData.length > 0 ? (
              <Tree<DictTreeNode>
                blockNode
                treeData={treeData}
                selectedKeys={selectedRow ? [selectedRow.id] : []}
                expandedKeys={expandedKeys}
                onSelect={(keys, info) => {
                  if (keys.length === 0) return;
                  const node = info.node as DictTreeNode;
                  applySelected(node.row);
                }}
                onExpand={(keys) => setExpandedKeys(keys)}
              />
            ) : (
              <Empty
                image={Empty.PRESENTED_IMAGE_SIMPLE}
                description="暂无字典类型"
              />
            )}
          </Spin>
        </Card>
      </Col>
      <Col span={16}>
        {selectedRow ? (
          <ProTable<DictRow>
            headerTitle={`字典项${selectedRow.label ? `【${selectedRow.label}】` : ''}`}
            actionRef={actionRef}
            rowKey="id"
            search={false}
            pagination={false}
            columns={itemColumns}
            params={{ dictId: selectedRow.id }}
            request={async () => {
              const current = selectedRef.current;
              if (!current) return { data: [], success: true, total: 0 };
              // getDictItemsByName 为名称模糊匹配，这里过滤出当前节点的直接子项
              const rows = await getDictItemsByName(current.name);
              const items = rows.filter((r) => r.parentId === current.id);
              return { data: items, success: true, total: items.length };
            }}
            toolBarRender={() => [
              can('dictionary:add') ? (
                <Button
                  key="createItem"
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={openCreateItemModal}
                >
                  新增字典项
                </Button>
              ) : null,
            ]}
          />
        ) : (
          <Card size="small">
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="请选择左侧字典类型"
            />
          </Card>
        )}
      </Col>

      <Modal
        title={
          modalMode === 'edit'
            ? '编辑字典'
            : modalMode === 'createType'
              ? '新增字典类型'
              : '新增字典项'
        }
        open={modalOpen}
        confirmLoading={submitting}
        forceRender
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ isActive: true, sort: 0 }}
        >
          <Form.Item
            name="name"
            label="字典名称"
            rules={[{ required: true, message: '请输入字典名称' }]}
          >
            <Input placeholder="请输入字典名称" />
          </Form.Item>
          <Form.Item name="label" label="字典标签">
            <Input placeholder="请输入字典标签" />
          </Form.Item>
          <Form.Item name="value" label="字典键值">
            <Input placeholder="请输入字典键值" />
          </Form.Item>
          <Form.Item name="sort" label="排序">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="isActive" label="是否启用" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>
    </Row>
  );
}
