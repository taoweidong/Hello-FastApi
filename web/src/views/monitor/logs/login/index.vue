<script setup lang="ts">
import { ADAPTIVE_OFFSET } from "@/config/adaptive";
import { computed, defineAsyncComponent, onMounted, ref } from "vue";
import dayjs from "dayjs";
import { useLoginLog } from "./hook";
import { getPickerShortcuts } from "../../utils";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { loadEcharts } from "@/plugins/echarts";
import { message } from "@/utils/message";
import { isNetworkLevelError } from "@/composables/useCrudTable";
import { getLoginLogsList } from "@/api/system/log";
import {
  getDashboardStats,
  type DashboardStats,
  type LoginTrendItem
} from "@/api/system/dashboard";

import Delete from "~icons/ep/delete";
import Refresh from "~icons/ep/refresh";

defineOptions({
  name: "LoginLog"
});

/*
 * 统计概览迷你趋势：与 welcome 图表同款懒加载——先 await loadEcharts()
 * 注册 echarts，再加载组件（useECharts 在 setup 时同步读取注册实例）。
 */
const MiniTrend = defineAsyncComponent(async () => {
  await loadEcharts();
  return import("./components/MiniTrend.vue");
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
} = useLoginLog(tableRef);

/* ===================== 统计概览（纯增量区块，不影响表格数据流） ===================== */

const stats = ref<DashboardStats | null>(null);

const loginTrend = computed<LoginTrendItem[]>(
  () => stats.value?.loginTrend ?? []
);

/** 今日登录次数文本（无数据显示 "—"） */
const todayLoginText = computed(() =>
  stats.value ? String(stats.value.todayStats.loginCount) : "—"
);

/** 近 7 日登录合计文本（loginTrend 求和；无数据显示 "—"） */
const weekLoginText = computed(() =>
  stats.value
    ? String(loginTrend.value.reduce((sum, item) => sum + item.count, 0))
    : "—"
);

/**
 * 登录成功率文本：近 7 日成功合计 / 近 7 日全部登录（含失败）。
 * /dashboard/stats 契约只有成功口径（loginCount/loginTrend 均为成功登录），
 * 总数用列表接口 pageSize=1 的 total 补齐；时间窗与后端 dashboard_service
 * 的 TREND_DAYS 口径对齐（含今日共 7 天，起始为 6 天前 00:00）。
 * 总数缺失或为 0 时显示 "—"。
 */
const successRateText = ref("—");

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
    getLoginLogsList({ pageNum: 1, pageSize: 1, createdTime })
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
    weekTotalRes.value.data &&
    stats.value
  ) {
    const total = weekTotalRes.value.data.total ?? 0;
    const success = loginTrend.value.reduce((sum, item) => sum + item.count, 0);
    // 分母取到且大于 0 才计算；成功率封顶 100%（仪表盘 60s 缓存与实时总数
    // 存在秒级窗口差，避免极端时序下出现 >100% 的观感）
    successRateText.value =
      total > 0
        ? `${Math.round((Math.min(success, total) / total) * 100)}%`
        : "—";
  }
  // 失败静默：网络层错误已由全局拦截器提示；仅业务错误轻提示一次
  for (const result of [statsRes, weekTotalRes]) {
    if (result.status === "rejected" && !isNetworkLevelError(result.reason)) {
      message("统计概览加载失败，请稍后重试", { type: "error" });
      break;
    }
  }
}

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
      <el-form-item label="登录类型" prop="loginType">
        <el-select
          v-model="form.loginType"
          placeholder="请选择登录类型"
          clearable
          class="w-full"
        >
          <el-option label="密码" value="0" />
          <el-option label="短信" value="1" />
          <el-option label="OAuth" value="2" />
        </el-select>
      </el-form-item>
      <el-form-item label="登录状态" prop="status">
        <el-select
          v-model="form.status"
          placeholder="请选择登录状态"
          clearable
          class="w-full"
        >
          <el-option label="成功" value="1" />
          <el-option label="失败" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item label="登录时间" prop="createdTime">
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

    <!-- 统计概览迷你条：搜索区与表格之间的纯增量区块，失败静默显示 "—" -->
    <div
      class="bg_bg_color w-full flex-bc flex-wrap gap-y-(--pure-space-2) rounded mb-(--pure-content-margin) px-(--pure-space-6) py-(--pure-space-3)"
    >
      <div
        class="flex items-center flex-wrap gap-x-(--pure-space-6) gap-y-(--pure-space-1) text-sm text-text_color_regular"
      >
        <span>
          今日登录
          <span class="font-semibold text-text_color_primary">
            {{ todayLoginText }}
          </span>
          次
        </span>
        <span>
          近 7 日合计
          <span class="font-semibold text-text_color_primary">
            {{ weekLoginText }}
          </span>
          次
        </span>
        <span>
          成功率
          <span class="font-semibold text-text_color_primary">
            {{ successRateText }}
          </span>
        </span>
      </div>
      <MiniTrend
        v-if="loginTrend.length"
        :data="loginTrend"
        class="w-55 shrink-0"
      />
    </div>

    <PureTableBar
      title="登录日志"
      :columns="columns"
      :tableRef="tableRef?.getTableRef()"
      @refresh="onSearch"
      @fullscreen="onFullscreen"
    >
      <template #buttons>
        <el-popconfirm title="确定要删除所有日志数据吗？" @confirm="clearAll">
          <template #reference>
            <el-button type="danger" :icon="useRenderIcon(Delete)">
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
              <el-button type="danger" text class="mr-1!"> 批量删除 </el-button>
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
