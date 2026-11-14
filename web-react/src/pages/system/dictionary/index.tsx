/** 字典管理页面：左侧字典类型树（搜索/节点操作）+ 右侧字典项列表（对齐 Vue useDictionary） */
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
  Divider,
  Empty,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Row,
  Spin,
  Switch,
  Tree,
} from 'antd';
import dayjs from 'dayjs';
import { useEffect, useMemo, useRef, useState } from 'react';
import {
  createDict,
  type DictPayload,
  type DictRow,
  deleteDict,
  getDictItemsByName,
  getDictionaries,
  updateDict,
} from '@/services/api';

/** 字典表单值（isActive 由 Switch 提供，为 boolean） */
interface DictFormValues {
  name?: string;
  label?: string;
  value?: string;
  sort?: number;
  isActive: boolean;
  description?: string;
}

/** antd Tree 节点（挂原始字典行，便于 onSelect 后取回数据） */
interface DictTreeNode {
  key: string;
  title: React.ReactNode;
  row: DictRow;
}

type DictModalMode = 'createType' | 'createItem' | 'edit';

/** 时间格式化（对齐 Vue dayjs YYYY-MM-DD HH:mm:ss） */
function fmtTime(v: string | null | undefined): string {
  return v ? dayjs(v).format('YYYY-MM-DD HH:mm:ss') : '-';
}

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

function errText(e: unknown): string {
  return e instanceof Error ? e.message : '操作失败';
}

export default function DictionaryPage(): React.ReactNode {
  const { message, modal } = App.useApp();
  const { initialState } = useModel('@@initialState');
  // 按钮级权限：超管直接放行（与 access.ts 的 isAdmin 口径一致），普通用户按权限码判断
  const can = (code: string): boolean =>
    initialState?.currentUser?.username === 'admin' ||
    (initialState?.permissions?.includes(code) ?? false);

  const actionRef = useRef<ActionType | undefined>(undefined);
  const selectedRef = useRef<DictRow | null>(null);
  const [form] = Form.useForm<DictFormValues>();
  const [treeSearch, setTreeSearch] = useState('');

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
      const roots = buildDictTree(rows);
      const prevId = selectedRef.current?.id;
      const next = prevId
        ? (rows.find((r) => r.id === prevId) ?? null)
        : (roots[0] ?? null);
      applySelected(next);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '加载字典失败');
    } finally {
      setTreeLoading(false);
    }
  }

  useEffect(() => {
    void loadTree();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 树数据变化后默认展开所有层级（对齐 Vue default-expand-all）
  const rootTypes = useMemo(() => buildDictTree(flatList), [flatList]);
  useEffect(() => {
    setExpandedKeys(rootTypes.map((r) => r.id));
  }, [rootTypes]);

  /** 左侧树过滤（对齐 Vue filterNode：name(value|label) 包含匹配） */
  const filteredRootTypes = useMemo(() => {
    const q = treeSearch.trim();
    if (!q) return rootTypes;
    return rootTypes.filter((r) =>
      `${r.name}(${r.value || r.label})`.includes(q),
    );
  }, [rootTypes, treeSearch]);

  /** 字典类型下是否有子项（对齐 Vue handleDeleteType 的前置校验） */
  function hasChildren(row: DictRow): boolean {
    return flatList.some((r) => r.parentId === row.id);
  }

  /** 新增字典类型（根级，parentId=0） */
  function openCreateTypeModal(): void {
    setModalMode('createType');
    setEditingRow(null);
    form.resetFields();
    setModalOpen(true);
  }

  /** 新增字典详情（子项，需先选中左侧类型） */
  function openCreateItemModal(): void {
    if (!selectedRef.current) {
      message.warning('请先选择左侧字典类型');
      return;
    }
    setModalMode('createItem');
    setEditingRow(null);
    form.resetFields();
    setModalOpen(true);
  }

  /** 从树节点新增字典详情 */
  function openCreateItemForNode(parentNode: DictRow): void {
    applySelected(parentNode);
    setModalMode('createItem');
    setEditingRow(null);
    form.resetFields();
    setModalOpen(true);
  }

  /** 修改字典项 */
  function openEditModal(row: DictRow): void {
    setModalMode('edit');
    setEditingRow(row);
    form.setFieldsValue({
      name: row.name,
      label: row.label,
      value: row.value,
      sort: row.sort,
      isActive: row.isActive === 1,
      description: row.description ?? '',
    });
    setModalOpen(true);
  }

  /** 删除字典类型（根节点，含子项校验，对齐 Vue handleDeleteType） */
  function handleDeleteType(row: DictRow): void {
    if (hasChildren(row)) {
      message.warning('该字典类型下有子项，请先删除子项');
      return;
    }
    modal.confirm({
      title: '系统提示',
      content: `确认要删除字典类型 ${row.name} 吗?`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deleteDict(row.id);
          message.success(`已成功删除字典类型 ${row.name}`);
          if (selectedRef.current?.id === row.id) applySelected(null);
          await loadTree();
          actionRef.current?.reload();
        } catch (e) {
          message.error(errText(e));
        }
      },
    });
  }

  /** 删除字典项（对齐 Vue handleDelete） */
  async function handleDeleteDict(row: DictRow): Promise<void> {
    try {
      await deleteDict(row.id);
      message.success(`已成功删除字典 ${row.label || row.name}`);
      await loadTree();
      actionRef.current?.reload();
    } catch (error) {
      message.error(error instanceof Error ? error.message : '删除失败');
    }
  }

  /** 字典项状态开关（对齐 Vue handleUpdateStatus：失败回滚） */
  async function handleToggleStatus(
    row: DictRow,
    checked: boolean,
  ): Promise<void> {
    const next = checked ? 1 : 0;
    try {
      await updateDict(row.id, {
        name: row.name,
        isActive: next,
        parentId: row.parentId,
      });
      message.success(`字典 ${row.label} 状态已更新`);
      await loadTree();
      actionRef.current?.reload();
    } catch {
      message.error('状态更新失败');
    }
  }

  async function handleSubmit(): Promise<void> {
    const values = await form.validateFields().catch(() => null);
    if (!values) return;
    setSubmitting(true);
    try {
      if (modalMode === 'edit' && editingRow) {
        const payload: DictPayload = {
          name: values.name ?? editingRow.name,
          label: values.label || '',
          value: values.value || '',
          sort: values.sort ?? null,
          isActive: values.isActive ? 1 : 0,
          description: values.description || null,
          // 后端更新时显式回传原父级，避免父级被误改
          parentId: editingRow.parentId,
        };
        await updateDict(editingRow.id, payload);
        message.success(`成功更新字典 ${values.label || values.name}`);
      } else if (modalMode === 'createItem' && selectedRef.current) {
        const parent = selectedRef.current;
        const payload: DictPayload = {
          name: parent.name,
          label: values.label || '',
          value: values.value || '',
          parentId: parent.id,
          sort: values.sort ?? null,
          isActive: values.isActive ? 1 : 0,
          description: values.description || null,
        };
        await createDict(payload);
        message.success(`成功创建字典详情 ${values.label || ''}`);
      } else {
        const payload: DictPayload = {
          name: values.name ?? '',
          label: values.label || '',
          value: values.value || '',
          parentId: null,
          sort: values.sort ?? null,
          isActive: values.isActive ? 1 : 0,
          description: values.description || null,
        };
        await createDict(payload);
        message.success(`成功创建字典类型 ${values.name || ''}`);
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

  /** 树节点标题：name (value)（对齐 Vue el-tree 节点渲染）+ 悬浮操作按钮 */
  function renderTreeNodeTitle(node: DictRow): React.ReactNode {
    const actions: React.ReactNode[] = [];
    if (can('dictionary:edit')) {
      actions.push(
        <Button
          key="edit"
          type="text"
          size="small"
          icon={<EditOutlined />}
          title="修改"
          onClick={() => openEditModal(node)}
        />,
      );
    }
    if (can('dictionary:add')) {
      actions.push(
        <Button
          key="addChild"
          type="text"
          size="small"
          icon={<PlusOutlined />}
          title="新增子项"
          onClick={() => openCreateItemForNode(node)}
        />,
      );
    }
    if (can('dictionary:delete')) {
      actions.push(
        <Button
          key="delete"
          type="text"
          size="small"
          danger
          icon={<DeleteOutlined />}
          title="删除"
          onClick={() => handleDeleteType(node)}
        />,
      );
    }
    return (
      <span
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 4,
          width: '100%',
        }}
      >
        <span
          style={{
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
          title={node.name}
        >
          {node.name}
          {node.value ? (
            <span
              style={{
                color: 'rgba(0, 0, 0, 0.45)',
                marginLeft: 4,
                fontSize: 12,
              }}
            >
              ({node.value})
            </span>
          ) : null}
        </span>
        {actions.length > 0 ? (
          <span onClick={(e) => e.stopPropagation()}>{actions}</span>
        ) : null}
      </span>
    );
  }

  /** 表单形态：根级字典类型 / 子项详情（对齐 Vue isRootType 切换校验） */
  const isRootForm =
    modalMode === 'createType' ||
    (modalMode === 'edit' && !editingRow?.parentId);

  /** 左侧树仅展示根级字典类型（对齐 Vue dictTypeList） */
  const treeData: DictTreeNode[] = filteredRootTypes.map((row) => ({
    key: row.id,
    row,
    title: renderTreeNodeTitle(row),
  }));

  const itemColumns: ProColumns<DictRow>[] = [
    { title: '字典标签', dataIndex: 'label', ellipsis: true },
    { title: '字典值', dataIndex: 'value', ellipsis: true },
    {
      title: '状态',
      dataIndex: 'isActive',
      width: 90,
      render: (_, record) => (
        <Switch
          checked={record.isActive === 1}
          checkedChildren="启用"
          unCheckedChildren="停用"
          disabled={!can('dictionary:edit')}
          onChange={(checked) => void handleToggleStatus(record, checked)}
        />
      ),
    },
    { title: '排序', dataIndex: 'sort', width: 80 },
    {
      title: '备注',
      dataIndex: 'description',
      ellipsis: true,
      render: (_, r) => r.description ?? '-',
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
      title: '操作',
      valueType: 'option',
      width: 120,
      render: (_, record) => [
        can('dictionary:edit') ? (
          <a key="edit" onClick={() => openEditModal(record)}>
            修改
          </a>
        ) : null,
        can('dictionary:delete') ? (
          <Popconfirm
            key="delete"
            title={`是否确认删除字典标签为${record.label}的这条数据`}
            onConfirm={() => void handleDeleteDict(record)}
          >
            <a style={{ color: '#ff4d4f' }}>删除</a>
          </Popconfirm>
        ) : null,
      ],
    },
  ];

  return (
    <Row gutter={16}>
      <Col xs={24} md={7}>
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
                新增类型
              </Button>
            ) : null
          }
        >
          <Input
            placeholder="请输入字典名称"
            allowClear
            value={treeSearch}
            onChange={(e) => setTreeSearch(e.target.value)}
            size="small"
          />
          <Divider style={{ margin: '8px 0' }} />
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
          <Divider style={{ margin: '8px 0' }} />
          {can('dictionary:add') ? (
            <Button
              type="primary"
              block
              icon={<PlusOutlined />}
              onClick={openCreateTypeModal}
            >
              新增类型
            </Button>
          ) : null}
        </Card>
      </Col>
      <Col xs={24} md={17}>
        {selectedRow ? (
          <ProTable<DictRow>
            headerTitle="字典管理"
            actionRef={actionRef}
            rowKey="id"
            search={false}
            pagination={false}
            columns={itemColumns}
            scroll={{ x: 'max-content' }}
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
                  key="createType"
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={openCreateTypeModal}
                >
                  新增字典
                </Button>
              ) : null,
              can('dictionary:add') ? (
                <Button key="createItem" onClick={openCreateItemModal}>
                  新增子项
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
            ? '修改字典'
            : modalMode === 'createType'
              ? '新增字典类型'
              : '新增字典详情'
        }
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
          initialValues={{ isActive: true, sort: null }}
        >
          {/* 根级字典类型才显示字典名称（必填）；子项显示所属字典（只读） */}
          {isRootForm ? (
            <Form.Item
              name="name"
              label="字典名称"
              rules={[{ required: true, message: '字典名称为必填项' }]}
            >
              <Input placeholder="请输入字典名称" />
            </Form.Item>
          ) : (
            <Form.Item label="所属字典">
              <Input
                value={
                  modalMode === 'createItem'
                    ? (selectedRow?.name ?? '')
                    : (editingRow?.name ?? '')
                }
                disabled
              />
            </Form.Item>
          )}
          <Form.Item
            name="label"
            label="显示标签"
            rules={
              isRootForm
                ? undefined
                : [{ required: true, message: '显示标签为必填项' }]
            }
          >
            <Input placeholder="请输入显示标签" />
          </Form.Item>
          <Form.Item name="value" label="字典值">
            <Input placeholder="请输入字典值" />
          </Form.Item>
          <Form.Item name="sort" label="排序">
            <InputNumber
              min={0}
              max={9999}
              precision={0}
              style={{ width: '100%' }}
              placeholder="不填自动递增"
            />
          </Form.Item>
          <Form.Item name="isActive" label="字典状态" valuePropName="checked">
            <Switch checkedChildren="启用" unCheckedChildren="停用" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea placeholder="请输入描述信息" rows={3} />
          </Form.Item>
        </Form>
      </Modal>
    </Row>
  );
}
