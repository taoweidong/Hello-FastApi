/**
 * 示例数据页（Univer 表格 CRUD 示例，1:1 对齐 Vue 版）：
 * - 表格即编辑面：加载后直接在单元格内修改；
 * - 「新增行」在表尾插入空行（ID 列留空标记为新增）；
 * - 「删除选中行」按当前选区删除（真实移除行，保存时按 ID 差异提交 deletes）；
 * - 「保存变更」读取整片数据与加载快照做差异 → 单事务批量回写
 *   （creates + updates + deletes）。
 * 公式引擎未配置 workerURL → 在主线程执行（数据网格无公式需求，省一个 Worker）。
 */
import {
  CheckOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useModel } from '@umijs/max';
import { UniverSheetsCorePreset } from '@univerjs/preset-sheets-core';
// 中文语言包（@univerjs/preset-sheets-core/locales/zh-CN，默认导出语言对象，facade 类型按模块扩充）
import UniverPresetSheetsCoreZhCN from '@univerjs/preset-sheets-core/locales/zh-CN';
import { createUniver, defaultTheme, LocaleType } from '@univerjs/presets';
import '@univerjs/preset-sheets-core/lib/index.css';
import { Alert, App, Button, Card, Space, Spin } from 'antd';
import { useEffect, useRef, useState } from 'react';
import {
  batchSaveExampleRows,
  type ExampleBatchSavePayload,
  type ExampleData,
  getExampleRows,
} from '@/services/api';

const UNIVER_CONTAINER = 'example-data-univer';
const HEADERS = ['ID', '名称', '类别', '数量', '单价', '记录日期', '备注'];
const COL_COUNT = HEADERS.length;
const COL_WIDTHS = [200, 180, 140, 100, 110, 130, 260];

/** Univer facade 类型按模块扩充（导入 preset 后生效），从 createUniver 返回值派生工作表类型 */
type UniverBundle = ReturnType<typeof createUniver>;
type UniverWorkbook = ReturnType<UniverBundle['univerAPI']['createWorkbook']>;
type UniverSheet = ReturnType<UniverWorkbook['getActiveSheet']>;

/** 单元格读出的行值（quantity/price 保持字符串提交，由后端 DTO 容错转换） */
interface SheetRowPayload {
  name: string;
  category: string;
  quantity: string;
  price: string;
  recordDate: string | null;
  note: string;
}
type SheetUpdatePayload = SheetRowPayload & { id: string; isActive: number };

/** 单元格原始值 → 规范化字符串（ID 列用于匹配，数值列由 DTO 层容错转换） */
function cellToString(v: unknown): string {
  if (v === null || v === undefined) return '';
  if (typeof v === 'object' && 'v' in (v as Record<string, unknown>)) {
    const inner = (v as Record<string, unknown>).v;
    return inner === null || inner === undefined ? '' : String(inner);
  }
  return String(v);
}

/** 分页循环拉全量（后端 pageSize 上限 100；最多 20 页 / 2000 行） */
async function fetchAllRows(): Promise<ExampleData[]> {
  const all: ExampleData[] = [];
  const pageSize = 100;
  for (let page = 1; page <= 20; page++) {
    const data = await getExampleRows({ pageNum: page, pageSize });
    all.push(...(data.list ?? []));
    if (all.length >= (data.total ?? 0)) break;
  }
  return all;
}

export default function ExampleDataPage(): React.ReactNode {
  const { message } = App.useApp();
  const { initialState } = useModel('@@initialState');
  const can = (code: string): boolean =>
    initialState?.permissions?.includes(code) ?? false;

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  // 顶部统计（rowIds 存 ref 非响应式 → 以 state 镜像展示）
  const [rowCount, setRowCount] = useState(0);
  const [dirtyCount, setDirtyCount] = useState(0);

  // Univer 实例句柄与数据快照（ref：变更不触发重渲染）
  const univerRef = useRef<{ dispose: () => void } | null>(null);
  const sheetRef = useRef<UniverSheet | null>(null);
  // 加载快照：rowIds[i] 与 snapshotRows[i] 对应表格第 i+1 行（0 为表头）
  const rowIdsRef = useRef<string[]>([]);
  const snapshotRowsRef = useRef<string[][]>([]);

  /** 重建 Univer 实例并返回活动工作表（dispose 会移除其内部 DOM 引用） */
  function initUniver(): UniverSheet {
    if (univerRef.current) {
      try {
        univerRef.current.dispose();
      } catch {
        /* 忽略重复释放 */
      }
      univerRef.current = null;
    }
    const container = document.getElementById(UNIVER_CONTAINER);
    if (container) container.innerHTML = '';

    const { univer, univerAPI } = createUniver({
      locale: LocaleType.ZH_CN,
      locales: {
        [LocaleType.ZH_CN]: UniverPresetSheetsCoreZhCN,
      },
      theme: defaultTheme,
      presets: [
        // 数据网格无需公式：不传 workerURL → 公式引擎在主线程执行
        UniverSheetsCorePreset({
          container: UNIVER_CONTAINER,
          header: false,
          toolbar: false,
          contextMenu: true,
        }),
      ],
    });
    univerRef.current = univer;
    const workbook = univerAPI.createWorkbook({ name: '示例数据表' });
    const sheet = workbook.getActiveSheet();
    sheet.setFrozenRows(1);
    sheet.getRange(0, 0, 1, COL_COUNT).setValues([HEADERS]);
    COL_WIDTHS.forEach((width, col) => {
      sheet.setColumnWidths(col, 1, width);
    });
    return sheet;
  }

  /** 把后端行写入表格数据区并记录快照 */
  function writeRows(rows: ExampleData[]): void {
    const sheet = sheetRef.current;
    if (!sheet) return;
    rowIdsRef.current = rows.map((r) => r.id);
    snapshotRowsRef.current = rows.map((r) => [
      r.id,
      r.name,
      r.category ?? '',
      String(r.quantity),
      String(r.price),
      r.recordDate ?? '',
      r.note ?? '',
    ]);
    const matrix = rows.map((r) => [
      r.id,
      r.name,
      r.category ?? '',
      r.quantity,
      r.price,
      r.recordDate ?? '',
      r.note ?? '',
    ]);
    // 先清空旧数据区（行数可能减少），再写入新矩阵
    sheet
      .getRange(1, 0, Math.max(1, rowIdsRef.current.length + 20), COL_COUNT)
      .setValues(
        Array.from({ length: Math.max(1, rowIdsRef.current.length + 20) }, () =>
          Array(COL_COUNT).fill(''),
        ),
      );
    if (matrix.length) {
      sheet.getRange(1, 0, matrix.length, COL_COUNT).setValues(matrix);
    }
    setDirtyCount(0);
    setRowCount(rowIdsRef.current.length);
  }

  /** 拉全量 → 重建表格 → 写入快照 */
  async function loadRows(): Promise<void> {
    setLoading(true);
    try {
      const rows = await fetchAllRows();
      sheetRef.current = initUniver();
      writeRows(rows);
    } catch {
      message.error('加载示例数据失败');
    } finally {
      setLoading(false);
    }
  }

  /** 在表尾插入一个空行（ID 列留空 → 保存时识别为新增） */
  function handleAddRow(): void {
    const sheet = sheetRef.current;
    if (!sheet) return;
    const insertAt = rowIdsRef.current.length + 1;
    sheet
      .getRange(insertAt, 1, 1, COL_COUNT - 1)
      .setValues([Array(COL_COUNT - 1).fill('')]);
    rowIdsRef.current.push('');
    snapshotRowsRef.current.push(['', '', '', '', '', '', '']);
    setRowCount(rowIdsRef.current.length);
    setDirtyCount((c) => c + 1);
  }

  /** 删除当前选区覆盖的数据行（真实移除行，保存时按 ID 差异提交 deletes） */
  function handleDeleteSelection(): void {
    const sheet = sheetRef.current;
    if (!sheet) return;
    const range = sheet.getSelection()?.getActiveRange();
    if (!range) {
      message.warning('请先在表格中选中要删除的行');
      return;
    }
    const startRow = range.getRow(); // 0 基；0 为表头
    const numRows = range.getHeight();
    const from = Math.max(1, startRow);
    const to = startRow + numRows - 1;
    if (to < 1) {
      message.warning('表头不可删除，请选中数据行');
      return;
    }
    const ids: string[] = [];
    for (let r = from; r <= to && r - 1 < rowIdsRef.current.length; r++) {
      const id = rowIdsRef.current[r - 1];
      if (id) ids.push(id);
    }
    sheet.deleteRows(from, to - from + 1);
    rowIdsRef.current = rowIdsRef.current.filter(
      (_, i) => i < from - 1 || i > to - 1,
    );
    snapshotRowsRef.current = snapshotRowsRef.current.filter(
      (_, i) => i < from - 1 || i > to - 1,
    );
    setRowCount(rowIdsRef.current.length);
    setDirtyCount((c) => c + ids.length);
    if (ids.length) {
      message.success(`已标记删除 ${ids.length} 行（保存后生效）`);
    }
  }

  /** 保存：整片读取 → 与快照逐行比对 → 单事务差异回写 */
  async function handleSave(): Promise<void> {
    const sheet = sheetRef.current;
    if (!sheet) return;
    setSaving(true);
    try {
      // 读取当前数据区（以 ID 列实际非空范围为准，容忍用户新增多行）
      let dataRowCount = rowIdsRef.current.length;
      for (let r = rowIdsRef.current.length; r >= 1; r--) {
        const id = cellToString(sheet.getRange(r, 0).getValues()[0][0]);
        if (id !== '') {
          dataRowCount = Math.max(dataRowCount, r);
          break;
        }
        if (r === 1) dataRowCount = 0;
      }
      // 至少读 1 行：全部是新增空行时（dataRowCount=0）也要统计“跳过空行”
      const range = sheet.getRange(1, 0, Math.max(1, dataRowCount), COL_COUNT);
      const raw = range.getValues();

      const creates: SheetRowPayload[] = [];
      const updates: SheetUpdatePayload[] = [];
      const currentIds: string[] = [];
      let skippedEmpty = 0;

      raw.forEach((cells, i) => {
        const id = cellToString(cells[0]);
        const name = cellToString(cells[1]).trim();
        const row = [
          cellToString(cells[2]),
          cellToString(cells[3]),
          cellToString(cells[4]),
          cellToString(cells[5]),
          cellToString(cells[6]),
        ];
        if (!id && !name) {
          skippedEmpty += 1;
          return;
        }
        currentIds.push(id);
        const original = snapshotRowsRef.current[i];
        if (!id) {
          creates.push({
            name,
            category: row[0],
            quantity: row[1],
            price: row[2],
            recordDate: row[3] || null,
            note: row[4],
          });
          return;
        }
        const changed =
          !original ||
          original[1] !== name ||
          original[2] !== row[0] ||
          original[3] !== row[1] ||
          original[4] !== row[2] ||
          original[5] !== row[3] ||
          original[6] !== row[4];
        if (changed) {
          updates.push({
            id,
            name,
            category: row[0],
            quantity: row[1],
            price: row[2],
            recordDate: row[3] || null,
            note: row[4],
            isActive: 1,
          });
        }
      });

      // 快照中有、当前表格中没有的 ID → 删除
      const deletes = rowIdsRef.current.filter(
        (id) => id && !currentIds.includes(id),
      );

      if (!creates.length && !updates.length && !deletes.length) {
        message.info(
          skippedEmpty
            ? `没有需要保存的变更（跳过 ${skippedEmpty} 个空行）`
            : '没有需要保存的变更',
        );
        return;
      }

      // quantity/price 以字符串提交（后端 DTO 容错转换），与 Vue 版行为一致
      const result = await batchSaveExampleRows({
        creates,
        updates,
        deletes,
      } as unknown as ExampleBatchSavePayload);
      message.success(
        `保存成功：新增 ${result.created}、更新 ${result.updated}、删除 ${result.deleted}`,
      );
      await loadRows();
    } catch {
      message.error('保存失败：名称重复或字段格式不正确');
    } finally {
      setSaving(false);
    }
  }

  useEffect(() => {
    void loadRows();
    // 组件卸载时释放 Univer 实例（dispose 会移除其内部 DOM 引用）
    return () => {
      if (univerRef.current) {
        try {
          univerRef.current.dispose();
        } catch {
          /* 忽略 */
        }
        univerRef.current = null;
      }
    };
  }, []);

  return (
    <Card
      title={
        <span style={{ fontWeight: 'bold' }}>
          示例数据表（Univer）
          <span
            style={{ marginLeft: 8, fontSize: 12, color: 'rgba(0,0,0,0.45)' }}
          >
            已加载 {rowCount} 行 · 未保存变更 {dirtyCount} 处
          </span>
        </span>
      }
      extra={
        <Space>
          {can('example:add') && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              disabled={saving}
              onClick={handleAddRow}
            >
              新增行
            </Button>
          )}
          {can('example:delete') && (
            <Button
              color="danger"
              variant="outlined"
              icon={<DeleteOutlined />}
              disabled={saving}
              onClick={handleDeleteSelection}
            >
              删除选中行
            </Button>
          )}
          {can('example:edit') && (
            <Button
              color="green"
              variant="solid"
              icon={<CheckOutlined />}
              loading={saving}
              onClick={() => void handleSave()}
            >
              保存变更
            </Button>
          )}
          {can('example:view') && (
            <Button
              type="text"
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={() => void loadRows()}
            >
              刷新
            </Button>
          )}
        </Space>
      }
    >
      <Alert
        type="info"
        showIcon
        closable={false}
        style={{ marginBottom: 12 }}
        title="直接在表格内编辑单元格；新增行后填写名称；选中行后点「删除选中行」；所有变更点「保存变更」一次性提交。"
      />
      <Spin spinning={loading}>
        <div id={UNIVER_CONTAINER} className="w-full" style={{ height: 620 }} />
      </Spin>
    </Card>
  );
}
