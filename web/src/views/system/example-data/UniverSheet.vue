<script setup lang="ts">
/*
 * Univer 电子表格子组件（2025 资源瘦身批次）：
 * 原先 example-data/index.vue 顶层静态 import @univerjs/presets /
 * preset-sheets-core 及其 CSS，导致约 6.7MB 的 Univer 代码被打进该页
 * chunk（虽有路由懒加载，但只要进入该页就在首屏请求时同步拉取）。
 * 现将全部 Univer 初始化/写入/差异计算逻辑下沉到本组件，由父页面
 * defineAsyncComponent 按需加载——只有真正进入示例数据表页才会拉取
 * Univer chunk 与 CSS，其它页面完全不受影响。
 *
 * 对父页面暴露的能力（defineExpose）：
 * - load():            拉取全量数据并重建表格（父页面控制 loading 遮罩）
 * - addRow():          表尾插入空行
 * - deleteSelection(): 按选区删除数据行
 * - save():            差异保存；返回 true 表示需要重新加载（父页面调用 load）
 * 状态上抛：loaded/dirty 变化时 emit("stat-change")，由父页面渲染统计文案。
 */
import { onBeforeUnmount, onMounted, ref } from "vue";
import { createUniver, defaultTheme, LocaleType } from "@univerjs/presets";
import { UniverSheetsCorePreset } from "@univerjs/preset-sheets-core";
// 中文语言包（@univerjs/preset-sheets-core/locales/zh-CN，默认导出语言对象）
import UniverPresetSheetsCoreZhCN from "@univerjs/preset-sheets-core/locales/zh-CN";
import "@univerjs/preset-sheets-core/lib/index.css";
import type { FWorksheet } from "@univerjs/sheets/facade";
import {
  batchSaveExampleRows,
  getExampleRows,
  type ExampleData
} from "@/api/system/example-data";
import { message } from "@/utils/message";

defineOptions({
  name: "UniverSheet"
});

const emit = defineEmits<{
  /** 组件挂载完成（异步 chunk 加载结束），父页面据此触发首次加载 */
  (e: "ready"): void;
  /** 行数/未保存变更数变化，父页面据此更新统计文案 */
  (e: "stat-change", stat: { loaded: number; dirty: number }): void;
}>();

/**
 * Univer 表格 CRUD 示例：
 * - 表格即编辑面：加载后直接在单元格内修改；
 * - 「新增行」在表尾插入空行（ID 列留空标记为新增）；
 * - 「删除选中行」按当前选区删除（真实移除行，保存时按 ID 差异提交 deletes）；
 * - 「保存变更」读取整片数据与加载快照做差异 → 单事务批量回写
 *   （creates + updates + deletes）。
 * 公式引擎未配置 workerURL → 在主线程执行（数据网格无公式需求，省一个 Worker）。
 */

const UNIVER_CONTAINER = "example-data-univer";
const HEADERS = ["ID", "名称", "类别", "数量", "单价", "记录日期", "备注"];
const COL_COUNT = HEADERS.length;
const COL_WIDTHS = [200, 180, 140, 100, 110, 130, 260];

const dirtyCount = ref(0);

// Univer 实例句柄（any：facade 类型按模块扩充，运行时含 createWorkbook）
let univerInstance: { dispose: () => void } | null = null;
let sheetRef: FWorksheet | null = null;
// 加载快照：rowIds[i] 与 snapshotRows[i] 对应表格第 i+1 行（0 为表头）
let rowIds: string[] = [];
let snapshotRows: string[][] = [];
// 供“删除选中行”定位数据行（选区删除后行数变化，以当前 ID 列为准做差异）

/** 上抛统计状态（父页面渲染"已加载 X 行 · 未保存变更 Y 处"） */
function emitStat(): void {
  emit("stat-change", { loaded: rowIds.length, dirty: dirtyCount.value });
}

/** 单元格原始值 → 规范化字符串（ID 列用于匹配，数值列由 DTO 层容错转换） */
function cellToString(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "object" && "v" in (v as Record<string, unknown>)) {
    const inner = (v as Record<string, unknown>).v;
    return inner === null || inner === undefined ? "" : String(inner);
  }
  return String(v);
}

async function initUniver(): Promise<FWorksheet> {
  // 重建实例前先释放旧的（dispose 会移除其内部 DOM 引用）
  if (univerInstance) {
    try {
      univerInstance.dispose();
    } catch {
      /* 忽略重复释放 */
    }
    univerInstance = null;
  }
  const container = document.getElementById(UNIVER_CONTAINER);
  if (container) container.innerHTML = "";

  const { univer, univerAPI } = createUniver({
    locale: LocaleType.ZH_CN,
    locales: {
      [LocaleType.ZH_CN]: UniverPresetSheetsCoreZhCN
    },
    theme: defaultTheme,
    presets: [
      // 数据网格无需公式：不传 workerURL → 公式引擎在主线程执行
      UniverSheetsCorePreset({
        container: UNIVER_CONTAINER,
        header: false,
        toolbar: false,
        contextMenu: true
      })
    ]
  });
  univerInstance = univer;
  const workbook = univerAPI.createWorkbook({ name: "示例数据表" });
  const sheet = workbook.getActiveSheet();
  sheet.setFrozenRows(1);
  sheet.getRange(0, 0, 1, COL_COUNT).setValues([HEADERS]);
  COL_WIDTHS.forEach((width, col) => {
    sheet.setColumnWidths(col, 1, width);
  });
  return sheet;
}

/** 把后端行写入表格数据区并记录快照 */
function writeRows(rows: ExampleData[]) {
  if (!sheetRef) return;
  rowIds = rows.map(r => r.id);
  snapshotRows = rows.map(r => [
    r.id,
    r.name,
    r.category ?? "",
    String(r.quantity),
    String(r.price),
    r.recordDate ?? "",
    r.note ?? ""
  ]);
  const matrix = rows.map(r => [
    r.id,
    r.name,
    r.category ?? "",
    r.quantity,
    r.price,
    r.recordDate ?? "",
    r.note ?? ""
  ]);
  // 先清空旧数据区（行数可能减少），再写入新矩阵
  sheetRef
    .getRange(1, 0, Math.max(1, rowIds.length + 20), COL_COUNT)
    .setValues(
      Array.from({ length: Math.max(1, rowIds.length + 20) }, () =>
        Array(COL_COUNT).fill("")
      )
    );
  if (matrix.length) {
    sheetRef.getRange(1, 0, matrix.length, COL_COUNT).setValues(matrix);
  }
  dirtyCount.value = 0;
}

/** 分页循环拉全量（后端 pageSize 上限 100；最多 20 页 / 2000 行） */
async function fetchAllRows(): Promise<ExampleData[]> {
  const all: ExampleData[] = [];
  const pageSize = 100;
  for (let page = 1; page <= 20; page++) {
    const { code, data } = await getExampleRows({ pageNum: page, pageSize });
    if (code !== 0 || !data) break;
    all.push(...(data.list ?? []));
    if (all.length >= (data.total ?? 0)) break;
  }
  return all;
}

/** 拉取数据并重建表格；失败提示由父/本组件统一为一条 error 消息 */
async function load(): Promise<void> {
  try {
    const rows = await fetchAllRows();
    sheetRef = await initUniver();
    writeRows(rows);
    emitStat();
  } catch {
    message("加载示例数据失败", { type: "error" });
  }
}

/** 在表尾插入一个空行（ID 列留空 → 保存时识别为新增） */
function addRow(): void {
  if (!sheetRef) return;
  const insertAt = rowIds.length + 1;
  sheetRef
    .getRange(insertAt, 1, 1, COL_COUNT - 1)
    .setValues([Array(COL_COUNT - 1).fill("")]);
  rowIds.push("");
  snapshotRows.push(["", "", "", "", "", "", ""]);
  dirtyCount.value += 1;
  emitStat();
}

/** 删除当前选区覆盖的数据行（真实移除行，保存时按 ID 差异提交 deletes） */
function deleteSelection(): void {
  if (!sheetRef) return;
  const selection = sheetRef.getSelection();
  const range = selection?.getActiveRange();
  if (!range) {
    message("请先在表格中选中要删除的行", { type: "warning" });
    return;
  }
  const startRow = range.getRow(); // 0 基；0 为表头
  const numRows = range.getHeight();
  const from = Math.max(1, startRow);
  const to = startRow + numRows - 1;
  if (to < 1) {
    message("表头不可删除，请选中数据行", { type: "warning" });
    return;
  }
  const ids = [];
  for (let r = from; r <= to && r - 1 < rowIds.length; r++) {
    const id = rowIds[r - 1];
    if (id) ids.push(id);
  }
  sheetRef.deleteRows(from, to - from + 1);
  rowIds = rowIds.filter((_, i) => i < from - 1 || i > to - 1);
  snapshotRows = snapshotRows.filter((_, i) => i < from - 1 || i > to - 1);
  dirtyCount.value += ids.length;
  emitStat();
  if (ids.length) {
    message(`已标记删除 ${ids.length} 行（保存后生效）`, { type: "success" });
  }
}

/** 保存：整片读取 → 与快照逐行比对 → 单事务差异回写；返回是否需要重新加载 */
async function save(): Promise<boolean> {
  if (!sheetRef) return false;
  try {
    // 读取当前数据区（以 ID 列实际非空范围为准，容忍用户新增多行）
    let dataRowCount = rowIds.length;
    for (let r = rowIds.length; r >= 1; r--) {
      const id = cellToString(sheetRef.getRange(r, 0).getValues()[0][0]);
      if (id !== "") {
        dataRowCount = Math.max(dataRowCount, r);
        break;
      }
      if (r === 1) dataRowCount = 0;
    }
    // 至少读 1 行：全部是新增空行时（dataRowCount=0）也要统计"跳过空行"
    const range = sheetRef.getRange(1, 0, Math.max(1, dataRowCount), COL_COUNT);
    const raw = range.getValues();

    const creates: Array<Record<string, unknown>> = [];
    const updates: Array<Record<string, unknown>> = [];
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
        cellToString(cells[6])
      ];
      if (!id && !name) {
        skippedEmpty += 1;
        return;
      }
      currentIds.push(id);
      const original = snapshotRows[i];
      if (!id) {
        creates.push({
          name,
          category: row[0],
          quantity: row[1],
          price: row[2],
          recordDate: row[3] || null,
          note: row[4]
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
          isActive: 1
        });
      }
    });

    // 快照中有、当前表格中没有的 ID → 删除
    const deletes = rowIds.filter(id => id && !currentIds.includes(id));

    if (!creates.length && !updates.length && !deletes.length) {
      message(
        skippedEmpty
          ? `没有需要保存的变更（跳过 ${skippedEmpty} 个空行）`
          : "没有需要保存的变更",
        {
          type: "info"
        }
      );
      return false;
    }

    const { code, data } = await batchSaveExampleRows({
      creates,
      updates,
      deletes
    } as never);
    if (code === 0) {
      message(
        `保存成功：新增 ${data?.created ?? 0}、更新 ${data?.updated ?? 0}、删除 ${data?.deleted ?? 0}`,
        { type: "success" }
      );
      // 保存成功后需要重新加载（父页面调用 load 并展示 loading 遮罩）
      return true;
    }
  } catch {
    message("保存失败：名称重复或字段格式不正确", { type: "error" });
  }
  return false;
}

onMounted(() => emit("ready"));

onBeforeUnmount(() => {
  if (univerInstance) {
    try {
      univerInstance.dispose();
    } catch {
      /* 忽略 */
    }
    univerInstance = null;
  }
});

defineExpose({ load, addRow, deleteSelection, save });
</script>

<template>
  <div :id="UNIVER_CONTAINER" class="h-155 w-full" />
</template>
