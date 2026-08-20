<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getServerInfo, type ServerInfo } from "@/api/system/monitor";
import { message } from "@/utils/message";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Refresh from "~icons/ep/refresh";

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

onMounted(() => fetchInfo());
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
                <div class="mt-2 text-gray-500">
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
                <div class="mt-2 text-gray-500">
                  总大小：{{ serverInfo.memory.total }}
                </div>
                <div class="text-gray-500">
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
                <div class="mt-2 text-gray-500">
                  总大小：{{ serverInfo.disk.total }}
                </div>
                <div class="text-gray-500">
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
  </div>
</template>
