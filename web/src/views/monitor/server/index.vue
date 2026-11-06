<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import {
  downloadLogFile,
  getLogFiles,
  getServerInfo,
  tailLogFile,
  type LogFileInfo,
  type ServerInfo
} from "@/api/system/monitor";
import { message } from "@/utils/message";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { deviceDetection } from "@pureadmin/utils";

import Download from "~icons/ep/download";
import Refresh from "~icons/ep/refresh";
import View from "~icons/ep/view";
import Fullscreen from "~icons/ri/fullscreen-fill";
import ExitFullscreen from "~icons/ri/fullscreen-exit-fill";

defineOptions({
  name: "ServerMonitor"
});

const loading = ref(false);
const serverInfo = ref<ServerInfo | null>(null);

/** 进度条百分比兜底（防止偶发越界值） */
function percent(value: number | undefined): number {
  return Math.min(Math.max(Math.round(value ?? 0), 0), 100);
}

/** 系统启动时间去掉 ISO 分隔符便于展示 */
function formatBootTime(value: string | undefined): string {
  return value ? value.replace("T", " ").slice(0, 19) : "-";
}

async function fetchInfo() {
  loading.value = true;
  try {
    const { data } = await getServerInfo();
    serverInfo.value = data ?? null;
  } catch {
    message("获取服务器监控数据失败", { type: "error" });
  } finally {
    loading.value = false;
  }
}

/** ====== 日志文件卡片（仅管理员可见，按钮按 monitor:manage 权限码显隐） ====== */
const logsLoading = ref(false);
const logFiles = ref<LogFileInfo[]>([]);
const tailDialog = reactive({
  visible: false,
  name: "",
  content: "",
  loading: false
});

function formatSize(sizeBytes: number): string {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = sizeBytes / 1024;
  let unitIdx = 0;
  while (value >= 1024 && unitIdx < units.length - 1) {
    value /= 1024;
    unitIdx += 1;
  }
  return `${value.toFixed(1)} ${units[unitIdx]}`;
}

async function fetchLogFiles() {
  logsLoading.value = true;
  try {
    const { data } = await getLogFiles();
    logFiles.value = data ?? [];
  } catch {
    // 非管理员/网络异常：卡片留空，不阻塞监控主体
    logFiles.value = [];
  } finally {
    logsLoading.value = false;
  }
}

/** 日志查看弹窗是否全屏（窄屏默认全屏，与项目其它弹窗的 deviceDetection 惯例一致） */
const tailFullscreen = ref(false);

function toggleTailFullscreen() {
  tailFullscreen.value = !tailFullscreen.value;
}

/** 拉取日志尾部内容：「打开」与「重新读取」共用，刷新时不重置全屏状态 */
async function loadTail(filename: string) {
  tailDialog.loading = true;
  tailDialog.content = "";
  try {
    const { data } = await tailLogFile(filename, 200);
    tailDialog.content = data?.content ?? "";
  } catch {
    message("读取日志尾部失败", { type: "error" });
    tailDialog.visible = false;
  } finally {
    tailDialog.loading = false;
  }
}

function openTail(filename: string) {
  tailDialog.name = filename;
  tailDialog.visible = true;
  tailFullscreen.value = deviceDetection();
  loadTail(filename);
}

/** 全屏状态下也能重新读取，不必关掉弹窗再打开 */
function refreshTail() {
  if (tailDialog.name) loadTail(tailDialog.name);
}

async function handleDownload(filename: string) {
  try {
    const blob = await downloadLogFile(filename);
    const url = URL.createObjectURL(new Blob([blob as unknown as BlobPart]));
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  } catch {
    message("下载失败：需要管理员权限", { type: "error" });
  }
}

onMounted(() => {
  fetchInfo();
  fetchLogFiles();
});
</script>

<template>
  <div>
    <el-card v-loading="loading" shadow="never">
      <template #header>
        <div class="flex-bc">
          <span class="font-bold">服务器监控</span>
          <el-button
            type="primary"
            text
            :icon="useRenderIcon(Refresh)"
            :loading="loading"
            @click="fetchInfo"
          >
            刷新
          </el-button>
        </div>
      </template>

      <template v-if="serverInfo">
        <!-- CPU / 内存 / 磁盘 使用率概览 -->
        <el-row :gutter="16">
          <el-col :xs="24" :sm="8">
            <el-card shadow="never" class="mb-4">
              <div class="text-center">
                <div class="mb-2 font-bold">CPU</div>
                <el-progress
                  type="dashboard"
                  :percentage="percent(serverInfo.cpu.usedPercent)"
                />
                <div class="mt-2 text-(--el-text-color-secondary)">
                  逻辑核心数：{{ serverInfo.cpu.coreCount }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-card shadow="never" class="mb-4">
              <div class="text-center">
                <div class="mb-2 font-bold">内存</div>
                <el-progress
                  type="dashboard"
                  :percentage="percent(serverInfo.memory.usedPercent)"
                />
                <div class="mt-2 text-(--el-text-color-secondary)">
                  总大小：{{ serverInfo.memory.total }}
                </div>
                <div class="text-(--el-text-color-secondary)">
                  已用：{{ serverInfo.memory.used }} / 可用：{{
                    serverInfo.memory.free
                  }}
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="8">
            <el-card shadow="never" class="mb-4">
              <div class="text-center">
                <div class="mb-2 font-bold">磁盘</div>
                <el-progress
                  type="dashboard"
                  :percentage="percent(serverInfo.disk.usedPercent)"
                />
                <div class="mt-2 text-(--el-text-color-secondary)">
                  总大小：{{ serverInfo.disk.total }}
                </div>
                <div class="text-(--el-text-color-secondary)">
                  已用：{{ serverInfo.disk.used }} / 可用：{{
                    serverInfo.disk.free
                  }}
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>

        <!-- 系统信息 -->
        <el-descriptions title="系统信息" :column="2" border class="mt-2">
          <el-descriptions-item label="主机名称">
            {{ serverInfo.system.hostname }}
          </el-descriptions-item>
          <el-descriptions-item label="操作系统">
            {{ serverInfo.system.osName }}
          </el-descriptions-item>
          <el-descriptions-item label="系统架构">
            {{ serverInfo.system.osArch }}
          </el-descriptions-item>
          <el-descriptions-item label="Python 版本">
            {{ serverInfo.system.pythonVersion }}
          </el-descriptions-item>
          <el-descriptions-item label="工作目录" :span="2">
            {{ serverInfo.system.workDir }}
          </el-descriptions-item>
          <el-descriptions-item label="系统启动时间" :span="2">
            {{ formatBootTime(serverInfo.system.bootTime) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 进程信息 -->
        <el-descriptions title="服务进程" :column="2" border class="mt-4">
          <el-descriptions-item label="进程 ID">
            {{ serverInfo.process.pid }}
          </el-descriptions-item>
          <el-descriptions-item label="占用内存">
            {{ serverInfo.process.memoryUsed }}
          </el-descriptions-item>
          <el-descriptions-item label="CPU 使用率">
            {{ serverInfo.process.cpuPercent }}%
          </el-descriptions-item>
          <el-descriptions-item label="运行时长">
            {{ serverInfo.process.runningTime }}
          </el-descriptions-item>
        </el-descriptions>
      </template>
    </el-card>

    <!-- 日志文件（仅管理员：按钮按 monitor:manage 权限码显隐，后端 require_superuser 双重校验） -->
    <el-card v-loading="logsLoading" shadow="never" class="mt-4">
      <template #header>
        <div class="flex-bc">
          <span class="font-bold">日志文件</span>
          <el-button
            text
            :icon="useRenderIcon(Refresh)"
            :loading="logsLoading"
            @click="fetchLogFiles"
          >
            刷新日志
          </el-button>
        </div>
      </template>

      <el-table :data="logFiles" border stripe>
        <el-table-column
          label="文件名"
          prop="name"
          min-width="220"
          show-overflow-tooltip
        />
        <el-table-column label="大小" min-width="100" align="right">
          <template #default="{ row }">
            {{ formatSize(row.sizeBytes) }}
          </template>
        </el-table-column>
        <el-table-column label="最后修改" prop="modifiedTime" min-width="170" />
        <el-table-column label="操作" min-width="160" align="center">
          <template #default="{ row }">
            <el-button
              v-auth="'monitor:manage'"
              type="primary"
              text
              size="small"
              :icon="useRenderIcon(View)"
              @click="openTail(row.name)"
            >
              查看尾部
            </el-button>
            <el-button
              v-auth="'monitor:manage'"
              type="default"
              text
              size="small"
              :icon="useRenderIcon(Download)"
              @click="handleDownload(row.name)"
            >
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog
      v-model="tailDialog.visible"
      :fullscreen="tailFullscreen"
      class="log-tail-dialog"
      :class="{ 'log-tail-dialog--full': tailFullscreen }"
      width="860"
      top="6vh"
      @closed="tailFullscreen = false"
    >
      <template #header="{ titleId, titleClass }">
        <div class="flex-bc w-full pr-8">
          <span :id="titleId" :class="[titleClass, 'truncate']">
            日志尾部：{{ tailDialog.name }}
          </span>
          <div class="flex items-center gap-1 shrink-0">
            <el-button
              text
              size="small"
              :icon="useRenderIcon(Refresh)"
              :loading="tailDialog.loading"
              @click="refreshTail"
            >
              重新读取
            </el-button>
            <el-button
              text
              size="small"
              :icon="
                useRenderIcon(tailFullscreen ? ExitFullscreen : Fullscreen)
              "
              @click="toggleTailFullscreen"
            >
              {{ tailFullscreen ? "退出全屏" : "全屏查看" }}
            </el-button>
          </div>
        </div>
      </template>

      <div v-loading="tailDialog.loading" class="log-tail-body">
        <pre
          v-if="!tailDialog.loading"
          class="overflow-auto rounded bg-gray-950 p-3 text-gray-100 whitespace-pre-wrap break-all"
          :class="
            tailFullscreen
              ? 'flex-1 min-h-0 text-sm/6'
              : 'max-h-[60vh] text-xs/5'
          "
          >{{ tailDialog.content || "（空文件）" }}</pre>
      </div>
    </el-dialog>
  </div>
</template>

<style lang="scss">
/*
 * 全屏日志：Element Plus 的 fullscreen 只把弹窗铺到视口，正文区仍按内容高度收缩，
 * 这里让 header/body/pre 形成 flex 链，使 <pre> 真正撑满剩余高度（否则下方大片空白）。
 * 非 scoped：el-dialog 经 Teleport 挂到 body 下，scoped 的祖先作用域选择器不可靠；
 * 类名 log-tail-dialog--full 仅在本页全屏时存在，不会污染其它页面。
 */
.log-tail-dialog--full {
  display: flex;
  flex-direction: column;
  height: 100vh !important;
  margin: 0 !important;
  border-radius: 0;

  > .el-dialog__body {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
    padding-top: 8px;
    overflow: hidden;
  }

  .log-tail-body {
    display: flex;
    flex: 1;
    flex-direction: column;
    min-height: 0;
  }
}
</style>
