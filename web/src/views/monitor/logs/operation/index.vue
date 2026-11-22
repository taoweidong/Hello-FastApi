<script setup lang="ts">
import { ADAPTIVE_OFFSET } from "@/config/adaptive";
import { computed, onMounted, ref } from "vue";
import dayjs from "dayjs";
import { useOperationLog } from "./hook";
import { getPickerShortcuts } from "../../utils";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { message } from "@/utils/message";
import { isNetworkLevelError } from "@/composables/useCrudTable";
import { getOperationLogsList } from "@/api/system/log";
import {
  getDashboardStats,
  type DashboardStats,
  type OpDistItem
} from "@/api/system/dashboard";

import Delete from "~icons/ep/delete";
import Refresh from "~icons/ep/refresh";

defineOptions({
  name: "OperationLog"
});

const formRef = ref();
const tableRef = ref();

const {
  form,
  loading,
  columns,
  dataList,
  pagination,
  selectedNum,
  onSearch,
  clearAll,
  resetForm,
  onbatchDel,
  handleSizeChange,
  onSelectionCancel,
  handleCurrentChange,
  handleSelectionChange
} = useOperationLog(tableRef);

/* ===================== 统计概览（纯增量区块，不影响表格数据流） ===================== */

const stats = ref<DashboardStats | null>(null);

/** 今日操作次数文本（无数据显示 "—"） */
const todayOpText = computed(() =>
  stats.value ? String(stats.value.todayStats.opCount) : "—"
);

/**
 * 近 7 日操作合计文本：/dashboard/stats 无操作时序字段（opDistribution 是
 * TOP8 模块分布而非全量合计），用列表接口 pageSize=1 的 total 补齐，
 * 时间窗与后端 dashboard_service 的 TREND_DAYS 口径对齐（含今日共 7 天）。
 */
const weekOpText = ref("—");

/** TOP 模块名称文本（opDistribution 第一项；无数据显示 "—"） */
const topModuleText = computed(
  () => stats.value?.opDistribution?.[0]?.module ?? "—"
);

/** TOP5 模块（opDistribution 前五，按次数降序） */
const topModules = computed<OpDistItem[]>(() =>
  (stats.value?.opDistribution ?? []).slice(0, 5)
);

/** 迷你条形宽度百分比：以 TOP5 最大值（首位）为基准 */
function barWidth(count: number): number {
  const max = topModules.value[0]?.count ?? 0;
  return max > 0 ? Math.round((count / max) * 100) : 0;
}

async function fetchStats() {
  // 时间窗与后端仪表盘趋势口径一致：含今日共 7 天，起始为 6 天前 00:00
  const createdTime = [
    dayjs().subtract(6, "day").startOf("day").format("YYYY-MM-DD HH:mm:ss"),
    dayjs().format("YYYY-MM-DD HH:mm:ss")
  ];
  /*
   * 统计条与表格加载并行、互不阻塞；两条请求彼此独立，一条失败不影响另一条。
   * 参照 useCrudTable/welcome 模式：断网/超时/5xx 属网络层错误，已由全局响应
   * 拦截器统一提示，这里静默复位；仅业务错误做一次本地提示，展示占位 "—"。
   */
  const [statsRes, weekTotalRes] = await Promise.allSettled([
    getDashboardStats(),
    getOperationLogsList({ pageNum: 1, pageSize: 1, createdTime })
  ]);
  if (
    statsRes.status === "fulfilled" &&
    statsRes.value.code === 0 &&
    statsRes.value.data
  ) {
    stats.value = statsRes.value.data;
  }
  if (
    weekTotalRes.status === "fulfilled" &&
    weekTotalRes.value.code === 0 &&
    weekTotalRes.value.data
  ) {
    // 请求成功即以真实总数展示（0 也是有效数据）；失败保持占位 "—"
    weekOpText.value = String(weekTotalRes.value.data.total ?? 0);
  }
  // 失败静默：网络层错误已由全局拦截器提示；仅业务错误轻提示一次
  for (const result of [statsRes, weekTotalRes]) {
    if (result.status === "rejected" && !isNetworkLevelError(result.reason)) {
      message("统计概览加载失败，请稍后重试", { type: "error" });
      break;
    }
  }
}

onMounted(fetchStats);

/** 全屏切换后重算表格自适应高度（与其它列表页一致） */
function onFullscreen() {
  tableRef.value.setAdaptive();
}
</script>

<template>
  <div>
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full overflow-auto"
    >
      <el-form-item label="所属模块" prop="module">
        <el-input
          v-model="form.module"
          placeholder="请输入所属模块"
          clearable
          class="w-full"
        />
      </el-form-item>
      <el-form-item label="操作状态" prop="status">
        <el-select
          v-model="form.status"
          placeholder="请选择操作状态"
          clearable
          class="w-full"
        >
          <el-option label="成功" value="1" />
          <el-option label="失败" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item label="操作时间" prop="createdTime">
        <el-date-picker
          v-model="form.createdTime"
          :shortcuts="getPickerShortcuts()"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始日期时间"
          end-placeholder="结束日期时间"
        />
      </el-form-item>
      <el-form-item>
        <el-button
          type="primary"
          :icon="useRenderIcon('ri/search-line')"
          :loading="loading"
          @click="onSearch"
        >
          搜索
        </el-button>
        <el-button :icon="useRenderIcon(Refresh)" @click="resetForm(formRef)">
          重置
        </el-button>
      </el-form-item>
    </el-form>

    <!-- 统计概览迷你条：搜索区与表格之间的纯增量区块，失败静默显示 "—"；
         右侧为 TOP5 模块横向迷你条形（纯 div 宽度百分比，无 echarts） -->
    <div
      class="bg_bg_color w-full flex-bc flex-wrap gap-y-(--pure-space-2) rounded mb-(--pure-content-margin) px-(--pure-space-6) py-(--pure-space-3)"
    >
      <div
        class="flex items-center flex-wrap gap-x-(--pure-space-6) gap-y-(--pure-space-1) text-sm text-text_color_regular"
      >
        <span>
          今日操作
          <span class="font-semibold text-text_color_primary">
            {{ todayOpText }}
          </span>
          次
        </span>
        <span>
          近 7 日
          <span class="font-semibold text-text_color_primary">
            {{ weekOpText }}
          </span>
          次
        </span>
        <span>
          TOP 模块
          <span class="font-semibold text-text_color_primary">
            {{ topModuleText }}
          </span>
        </span>
      </div>
      <div
        v-if="topModules.length"
        class="w-60 shrink-0 flex flex-col gap-(--pure-space-1)"
      >
        <div
          v-for="(item, index) in topModules"
          :key="item.module"
          class="flex items-center gap-(--pure-space-2) text-xs text-text_color_regular"
        >
          <span class="w-14 truncate text-right">{{ item.module }}</span>
          <div
            class="flex-1 h-1.5 bg-(--el-fill-color-light) rounded-full overflow-hidden"
          >
            <div
              class="h-full bg-primary rounded-full"
              :style="{
                width: `${barWidth(item.count)}%`,
                opacity: 1 - index * 0.12
              }"
            />
          </div>
        </div>
      </div>
    </div>

    <PureTableBar
      title="操作日志"
      :columns="columns"
      :tableRef="tableRef?.getTableRef()"
      @refresh="onSearch"
      @fullscreen="onFullscreen"
    >
      <template #buttons>
        <el-popconfirm title="确定要删除所有日志数据吗？" @confirm="clearAll">
          <template #reference>
            <el-button
              v-auth="'log:delete'"
              type="danger"
              :icon="useRenderIcon(Delete)"
            >
              清空日志
            </el-button>
          </template>
        </el-popconfirm>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <div
          v-if="selectedNum > 0"
          v-motion-fade
          class="bg-(--el-fill-color-light) w-full h-11.5 mb-2 pl-4 flex items-center"
        >
          <div class="flex-auto">
            <span
              style="font-size: var(--el-font-size-base)"
              class="text-[rgba(42,46,54,0.5)] dark:text-[rgba(220,220,242,0.5)]"
            >
              已选 {{ selectedNum }} 项
            </span>
            <el-button type="primary" text @click="onSelectionCancel">
              取消选择
            </el-button>
          </div>
          <el-popconfirm title="是否确认删除?" @confirm="onbatchDel">
            <template #reference>
              <el-button v-auth="'log:delete'" type="danger" text class="mr-1!">
                批量删除
              </el-button>
            </template>
          </el-popconfirm>
        </div>
        <pure-table
          ref="tableRef"
          row-key="id"
          showOverflowTooltip
          align-whole="center"
          table-layout="auto"
          :loading="loading"
          :size="size"
          adaptive
          :adaptiveConfig="{ offsetBottom: ADAPTIVE_OFFSET.withSelectionBar }"
          :data="dataList"
          :columns="dynamicColumns"
          :pagination="{ ...pagination, size }"
          @selection-change="handleSelectionChange"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        />
      </template>
    </PureTableBar>
  </div>
</template>
