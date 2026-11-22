<script setup lang="ts">
/*
 * 示例数据表页面（2025 资源瘦身批次重构）：
 * - Univer 初始化/写入/差异计算逻辑全部移入同目录 UniverSheet.vue；
 * - 本组件用 defineAsyncComponent 按需加载子组件——Univer 全家桶（约
 *   6.7MB）及其 CSS 只有真正进入本页才开始拉取，加载期间用 el-skeleton
 *   骨架占位（见下方 SheetSkeleton / loadingComponent）；
 * - 本页保留按钮（含 v-auth 权限指令）与统计文案，通过 ref 调用子组件
 *   暴露的 load/addRow/deleteSelection/save（defineExpose），行数/未保存
 *   变更数由子组件 stat-change 事件上抛。
 */
import { computed, defineAsyncComponent, defineComponent, h, ref } from "vue";
// 骨架占位直接引入（el-skeleton 走全局注册也可，但此处渲染函数场景直接引更稳）
import { ElSkeleton } from "element-plus";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import AddFill from "~icons/ep/plus";
import Delete from "~icons/ep/delete";
import Refresh from "~icons/ep/refresh";
import Save from "~icons/ep/check";

defineOptions({
  name: "ExampleData"
});

/** Univer chunk 加载期间的骨架占位（行数近似表格高度，animated 播放动画） */
const SheetSkeleton = defineComponent({
  name: "SheetSkeleton",
  render() {
    return h(ElSkeleton, {
      animated: true,
      rows: 12,
      style: { height: "100%", paddingTop: "8px" }
    });
  }
});

// Univer 表格子组件按需加载：loadingComponent 提供骨架占位，delay=0 立即显示
const UniverSheet = defineAsyncComponent({
  loader: () => import("./UniverSheet.vue"),
  loadingComponent: SheetSkeleton,
  delay: 0
});

const sheetRef = ref();
const loading = ref(false);
const saving = ref(false);
// 子组件上抛的统计状态（已加载行数 / 未保存变更数）
const stat = ref({ loaded: 0, dirty: 0 });
const statText = computed(
  () => `已加载 ${stat.value.loaded} 行 · 未保存变更 ${stat.value.dirty} 处`
);

/** 子组件就绪（异步 chunk 加载完成）后触发首次加载 */
function handleReady() {
  loadRows();
}

/** 加载数据并重建表格（loading 同时驱动子组件遮罩与刷新按钮 spinner） */
async function loadRows() {
  loading.value = true;
  try {
    await sheetRef.value?.load();
  } finally {
    loading.value = false;
  }
}

function handleAddRow() {
  sheetRef.value?.addRow();
}

function handleDeleteSelection() {
  sheetRef.value?.deleteSelection();
}

/** 保存变更；子组件返回 true 表示保存成功需要重新加载 */
async function handleSave() {
  saving.value = true;
  try {
    const needReload = await sheetRef.value?.save();
    if (needReload) await loadRows();
  } finally {
    saving.value = false;
  }
}
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
              :disabled="saving || loading"
              @click="handleAddRow"
            >
              新增行
            </el-button>
            <el-button
              v-auth="'example:delete'"
              type="danger"
              plain
              :icon="useRenderIcon(Delete)"
              :disabled="saving || loading"
              @click="handleDeleteSelection"
            >
              删除选中行
            </el-button>
            <el-button
              v-auth="'example:edit'"
              type="success"
              :icon="useRenderIcon(Save)"
              :loading="saving"
              :disabled="loading"
              @click="handleSave"
            >
              保存变更
            </el-button>
            <el-button
              v-auth="'example:view'"
              text
              :icon="useRenderIcon(Refresh)"
              :loading="loading"
              :disabled="saving"
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

      <UniverSheet
        ref="sheetRef"
        v-loading="loading"
        @ready="handleReady"
        @stat-change="
          s => {
            stat = s;
          }
        "
      />
    </el-card>
  </div>
</template>
