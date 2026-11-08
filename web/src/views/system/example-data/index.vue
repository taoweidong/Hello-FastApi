<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
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
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import AddFill from "~icons/ep/plus";
import Delete from "~icons/ep/delete";
import Refresh from "~icons/ep/refresh";
import Save from "~icons/ep/check";

defineOptions({
  name: "ExampleData"
});

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

const loading = ref(false);
const saving = ref(false);
const containerReady = ref(false);
const dirtyCount = ref(0);

// Univer 实例句柄（any：facade 类型按模块扩充，运行时含 createWorkbook）
let univerInstance: { dispose: () => void } | null = null;
let sheetRef: FWorksheet | null = null;
// 加载快照：rowIds[i] 与 snapshotRows[i] 对应表格第 i+1 行（0 为表头）
let rowIds: string[] = [];
let snapshotRows: string[][] = [];
// 供“删除选中行”定位数据行（选区删除后行数变化，以当前 ID 列为准做差异）
const statText = computed(
  () => `已加载 ${rowIds.length} 行 · 未保存变更 ${dirtyCount.value} 处`
);

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

async function loadRows() {
  loading.value = true;
  try {
    const rows = await fetchAllRows();
    sheetRef = await initUniver();
    writeRows(rows);
    containerReady.value = true;
  } catch {
    message("加载示例数据失败", { type: "error" });
  } finally {
    loading.value = false;
  }
}

/** 在表尾插入一个空行（ID 列留空 → 保存时识别为新增） */
function handleAddRow() {
  if (!sheetRef) return;
  const insertAt = rowIds.length + 1;
  sheetRef
    .getRange(insertAt, 1, 1, COL_COUNT - 1)
    .setValues([Array(COL_COUNT - 1).fill("")]);
  rowIds.push("");
  snapshotRows.push(["", "", "", "", "", "", ""]);
  dirtyCount.value += 1;
}

/** 删除当前选区覆盖的数据行（真实移除行，保存时按 ID 差异提交 deletes） */
function handleDeleteSelection() {
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
  if (ids.length) {
    message(`已标记删除 ${ids.length} 行（保存后生效）`, { type: "success" });
  }
}

/** 保存：整片读取 → 与快照逐行比对 → 单事务差异回写 */
async function handleSave() {
  if (!sheetRef) return;
  saving.value = true;
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
      return;
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
      await loadRows();
    }
  } catch {
    message("保存失败：名称重复或字段格式不正确", { type: "error" });
  } finally {
    saving.value = false;
  }
}

onMounted(() => loadRows());

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
</script>

<template>
  <div>
    <el-card shadow="never">
      <template #header>
        <div class="flex-bc">
          <span class="font-bold">
            示例数据表（Univer）
            <span class="text-xs text-gray-400 ml-2">{{ statText }}</span>
          </span>
          <div>
            <el-button
              v-auth="'example:add'"
              type="primary"
              :icon="useRenderIcon(AddFill)"
              :disabled="saving"
              @click="handleAddRow"
            >
              新增行
            </el-button>
            <el-button
              v-auth="'example:delete'"
              type="danger"
              plain
              :icon="useRenderIcon(Delete)"
              :disabled="saving"
              @click="handleDeleteSelection"
            >
              删除选中行
            </el-button>
            <el-button
              v-auth="'example:edit'"
              type="success"
              :icon="useRenderIcon(Save)"
              :loading="saving"
              @click="handleSave"
            >
              保存变更
            </el-button>
            <el-button
              v-auth="'example:view'"
              text
              :icon="useRenderIcon(Refresh)"
              :loading="loading"
              @click="loadRows"
            >
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        class="mb-3"
        title="直接在表格内编辑单元格；新增行后填写名称；选中行后点「删除选中行」；所有变更点「保存变更」一次性提交。"
      />

      <div :id="UNIVER_CONTAINER" v-loading="loading" class="h-155 w-full" />
    </el-card>
  </div>
</template>
