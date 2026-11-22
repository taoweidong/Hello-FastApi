<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted, ref } from "vue";
import ReCol from "@/components/ReCol";
import StatCard from "@/components/ReStatCard";
import ChartCard from "@/components/ReChartCard";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { loadEcharts } from "@/plugins/echarts";
import Refresh from "~icons/ep/refresh";
import { message } from "@/utils/message";
import { isNetworkLevelError } from "@/composables/useCrudTable";
import { dayjs } from "./utils";
import {
  getDashboardStats,
  type DashboardStats,
  type LoginTrendItem,
  type OpDistItem
} from "@/api/system/dashboard";

defineOptions({
  name: "Welcome"
});

/*
 * echarts 懒加载：全站只有本页用图表，不在 main.ts 启动即注册。
 * 图表组件改为异步组件——渲染前先 await loadEcharts() 动态加载 echarts
 * 并注册到 globalProperties.$echarts（@pureadmin/utils 的 useECharts
 * 在组件 setup 时同步读取该属性，必须先于子组件 setup 完成注册），
 * 同时图表代码本身也被拆进按需加载的 chunk。
 */
const ChartLine = defineAsyncComponent(async () => {
  await loadEcharts();
  return import("./components/charts/ChartLine.vue");
});
const ChartPie = defineAsyncComponent(async () => {
  await loadEcharts();
  return import("./components/charts/ChartPie.vue");
});

const loading = ref(false);
const stats = ref<DashboardStats | null>(null);

const loginTrend = computed<LoginTrendItem[]>(
  () => stats.value?.loginTrend ?? []
);
const opDistribution = computed<OpDistItem[]>(
  () => stats.value?.opDistribution ?? []
);
const recentLogs = computed(() => stats.value?.recentLogs ?? []);

/*
 * 统计卡配置：图标全部取自 offlineIconNames 白名单（离线渲染，不发在线请求）；
 * 颜色走 EP 语义色变量，深色模式随 html.dark 自动适配。
 */
const statCards = computed(() => {
  const totals = stats.value?.totals;
  const today = stats.value?.todayStats;
  return [
    {
      key: "users",
      title: "用户总数",
      icon: "ri/admin-line",
      value: totals?.users ?? 0,
      suffix: "人",
      iconColor: "var(--el-color-primary)",
      iconBg: "var(--el-color-primary-light-9)"
    },
    {
      key: "online",
      title: "在线人数",
      icon: "ri/radio-button-line",
      value: totals?.online ?? 0,
      suffix: "人",
      iconColor: "var(--el-color-success)",
      iconBg: "var(--el-color-success-light-9)"
    },
    {
      key: "login",
      title: "今日登录",
      icon: "ri/checkbox-circle-line",
      value: today?.loginCount ?? 0,
      suffix: "次",
      iconColor: "var(--el-color-warning)",
      iconBg: "var(--el-color-warning-light-9)"
    },
    {
      key: "op",
      title: "今日操作",
      icon: "ri/edit-box-line",
      value: today?.opCount ?? 0,
      suffix: "次",
      iconColor: "var(--el-color-danger)",
      iconBg: "var(--el-color-danger-light-9)"
    },
    {
      key: "roles",
      title: "角色数",
      icon: "ri/shield-keyhole-line",
      value: totals?.roles ?? 0,
      suffix: "个",
      iconColor: "var(--el-color-primary-light-3)",
      iconBg: "var(--el-color-primary-light-9)"
    },
    {
      key: "depts",
      title: "部门数",
      icon: "ri/mind-map",
      value: totals?.depts ?? 0,
      suffix: "个",
      iconColor: "var(--el-color-primary-dark-2)",
      iconBg: "var(--el-color-primary-light-9)"
    }
  ];
});

/** 数据构成：各实体占五类条目总数的百分比（条纹进度条沿用原 progressData 卡片风格） */
const compositionItems = computed(() => {
  const totals = stats.value?.totals;
  const items = [
    {
      name: "用户",
      count: totals?.users ?? 0,
      color: "var(--el-color-primary)"
    },
    {
      name: "角色",
      count: totals?.roles ?? 0,
      color: "var(--el-color-primary-light-3)"
    },
    {
      name: "菜单",
      count: totals?.menus ?? 0,
      color: "var(--el-color-primary-light-5)"
    },
    {
      name: "部门",
      count: totals?.depts ?? 0,
      color: "var(--el-color-primary-light-7)"
    },
    {
      name: "岗位",
      count: totals?.posts ?? 0,
      color: "var(--el-color-primary-dark-2)"
    }
  ];
  const total = items.reduce((sum, item) => sum + item.count, 0);
  return items.map(item => ({
    ...item,
    percentage: total > 0 ? Math.round((item.count / total) * 100) : 0
  }));
});

/*
 * 条内文字阈值：窄进度条（stroke-width 21）放不下短文字，小百分比时
 * "N%" 会被裁切成残字（1% 只剩 "("、0% 几乎不可见）。
 * <15% 隐藏条内文字并把百分比并入右侧说明，≥15% 维持条内文字。
 */
const BAR_TEXT_MIN_PERCENTAGE = 15;

/** el-progress format：<15% 返回空串隐藏条内文字，≥15% 维持默认百分比文案 */
function barTextFormat(percentage: number): string {
  return percentage >= BAR_TEXT_MIN_PERCENTAGE ? `${percentage}%` : "";
}

/** 右侧说明：≥15% 条内已有百分比不重复；<15% 条内为空，把百分比并入右侧 */
function compositionLabel(item: {
  name: string;
  count: number;
  percentage: number;
}): string {
  return item.percentage >= BAR_TEXT_MIN_PERCENTAGE
    ? `${item.name} · ${item.count}`
    : `${item.name} · ${item.count}（${item.percentage}%）`;
}

/** 请求方法 → el-tag 语义色 */
type MethodTagType = "primary" | "success" | "warning" | "danger" | "info";

const METHOD_TAG_TYPES: Record<string, MethodTagType> = {
  GET: "info",
  POST: "primary",
  PUT: "warning",
  DELETE: "danger",
  PATCH: "warning"
};

function methodTagType(method: string): MethodTagType {
  return METHOD_TAG_TYPES[method?.toUpperCase()] ?? "info";
}

/** 状态码文本颜色：非 200 红色文本（null 显示灰色占位） */
function statusCodeStyle(statusCode: number | null) {
  return statusCode !== null && statusCode !== 200
    ? { color: "var(--el-color-danger)", fontWeight: 600 }
    : {};
}

/** 时间列紧凑格式化 */
function formatLogTime(value: string) {
  return value ? dayjs(value).format("MM-DD HH:mm") : "-";
}

async function fetchStats() {
  loading.value = true;
  try {
    const { code, data } = await getDashboardStats();
    if (code === 0 && data) {
      stats.value = data;
    }
  } catch (error) {
    /*
     * 参照 useCrudTable 模式：断网/超时/5xx 属网络层错误，已由全局响应
     * 拦截器统一提示，这里静默复位 loading；仅 4xx 业务错误做本地提示。
     * 失败时保留旧数据（首次失败则保持 null），页面呈现空态而非白屏。
     */
    if (!isNetworkLevelError(error)) {
      message("仪表盘数据加载失败，请稍后重试", { type: "error" });
    }
  } finally {
    loading.value = false;
  }
}

onMounted(fetchStats);
</script>

<template>
  <div v-loading="loading">
    <el-row :gutter="24" justify="space-around">
      <!-- 行1：统计卡（xs=12 双列换行，其余单行 6 列） -->
      <re-col
        v-for="(item, index) in statCards"
        :key="item.key"
        v-motion
        class="mb-4.5"
        :value="4"
        :xs="12"
        :initial="{
          opacity: 0,
          y: 100
        }"
        :enter="{
          opacity: 1,
          y: 0,
          transition: {
            delay: 80 * (index + 1)
          }
        }"
      >
        <StatCard
          :title="item.title"
          :icon="item.icon"
          :value="item.value"
          :suffix="item.suffix"
          :iconColor="item.iconColor"
          :iconBg="item.iconBg"
        />
      </re-col>

      <!-- 行2 左：近 7 日登录趋势（刷新入口放在首个图表卡 actions） -->
      <re-col
        v-motion
        class="mb-4.5"
        :value="16"
        :xs="24"
        :initial="{
          opacity: 0,
          y: 100
        }"
        :enter="{
          opacity: 1,
          y: 0,
          transition: {
            delay: 560
          }
        }"
      >
        <ChartCard title="近 7 日登录趋势" subtitle="按天统计登录次数">
          <template #actions>
            <el-button
              size="small"
              text
              type="primary"
              :icon="useRenderIcon(Refresh)"
              :loading="loading"
              @click="fetchStats"
            >
              刷新
            </el-button>
          </template>
          <ChartLine v-if="loginTrend.length" :data="loginTrend" />
          <el-empty
            v-else
            description="暂无登录趋势数据"
            :image-size="90"
            class="py-6"
          />
        </ChartCard>
      </re-col>

      <!-- 行2 右：操作模块分布 -->
      <re-col
        v-motion
        class="mb-4.5"
        :value="8"
        :xs="24"
        :initial="{
          opacity: 0,
          y: 100
        }"
        :enter="{
          opacity: 1,
          y: 0,
          transition: {
            delay: 640
          }
        }"
      >
        <ChartCard title="操作模块分布" subtitle="TOP 8">
          <ChartPie v-if="opDistribution.length" :data="opDistribution" />
          <el-empty
            v-else
            description="暂无操作数据"
            :image-size="90"
            class="py-6"
          />
        </ChartCard>
      </re-col>

      <!-- 行3 左：最近操作日志 -->
      <re-col
        v-motion
        class="mb-4.5"
        :value="16"
        :xs="24"
        :initial="{
          opacity: 0,
          y: 100
        }"
        :enter="{
          opacity: 1,
          y: 0,
          transition: {
            delay: 720
          }
        }"
      >
        <ChartCard title="最近操作日志" :minHeight="360">
          <el-table :data="recentLogs" size="small">
            <el-table-column
              label="模块"
              prop="module"
              min-width="90"
              show-overflow-tooltip
            />
            <el-table-column label="方法" width="82">
              <template #default="{ row }">
                <el-tag
                  size="small"
                  effect="plain"
                  :type="methodTagType(row.method)"
                >
                  {{ row.method }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              label="路径"
              prop="path"
              min-width="150"
              show-overflow-tooltip
            />
            <el-table-column
              label="IP"
              prop="ipaddress"
              min-width="110"
              show-overflow-tooltip
            />
            <el-table-column
              label="操作人"
              prop="creator"
              min-width="80"
              show-overflow-tooltip
            />
            <el-table-column label="状态" width="70">
              <template #default="{ row }">
                <span
                  v-if="row.statusCode !== null"
                  class="text-sm"
                  :style="statusCodeStyle(row.statusCode)"
                >
                  {{ row.statusCode }}
                </span>
                <span v-else class="text-sm text-text_color_regular">-</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="110">
              <template #default="{ row }">
                <span class="text-sm text-text_color_regular">
                  {{ formatLogTime(row.createdTime) }}
                </span>
              </template>
            </el-table-column>
            <template #empty>
              <el-empty description="暂无操作日志" :image-size="90" />
            </template>
          </el-table>
        </ChartCard>
      </re-col>

      <!-- 行3 右：数据构成 -->
      <re-col
        v-motion
        class="mb-4.5"
        :value="8"
        :xs="24"
        :initial="{
          opacity: 0,
          y: 100
        }"
        :enter="{
          opacity: 1,
          y: 0,
          transition: {
            delay: 800
          }
        }"
      >
        <ChartCard
          title="数据构成"
          subtitle="各实体占总条目比例"
          :minHeight="360"
        >
          <div
            v-for="(item, index) in compositionItems"
            :key="item.name"
            class="flex-bc"
            :class="index === 0 ? '' : 'mt-(--pure-space-4)'"
          >
            <el-progress
              class="w-[85%]!"
              :text-inside="true"
              :percentage="item.percentage"
              :stroke-width="21"
              :color="item.color"
              :format="barTextFormat"
              striped
              striped-flow
              :duration="10"
            />
            <span class="text-nowrap ml-2 text-text_color_regular text-sm">
              {{ compositionLabel(item) }}
            </span>
          </div>
        </ChartCard>
      </re-col>
    </el-row>
  </div>
</template>
