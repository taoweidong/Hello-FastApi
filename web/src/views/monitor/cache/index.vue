<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getCacheInfo, type CacheInfo } from "@/api/system/monitor";
import { message } from "@/utils/message";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Refresh from "~icons/ep/refresh";

defineOptions({
  name: "CacheMonitor"
});

const loading = ref(false);
const cacheInfo = ref<CacheInfo | null>(null);

/** 将运行秒数格式化为可读时长 */
function formatUptime(seconds: number | undefined): string {
  if (!seconds) return "-";
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  const parts: Array<string> = [];
  if (days > 0) parts.push(`${days}天`);
  if (hours > 0) parts.push(`${hours}小时`);
  if (minutes > 0) parts.push(`${minutes}分钟`);
  parts.push(`${secs}秒`);
  return parts.join("");
}

async function fetchInfo() {
  loading.value = true;
  try {
    const { data } = await getCacheInfo();
    cacheInfo.value = data ?? null;
  } catch {
    message("获取缓存监控数据失败", { type: "error" });
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
          <span class="font-bold">缓存监控</span>
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

      <!-- Redis 不可用时降级提示 -->
      <el-result
        v-if="cacheInfo && !cacheInfo.connected"
        icon="warning"
        title="缓存服务不可用"
        :sub-title="cacheInfo.message || 'Redis 未启动或未配置'"
      />

      <template v-else-if="cacheInfo">
        <el-descriptions title="Redis 运行状态" :column="3" border>
          <el-descriptions-item label="版本">
            {{ cacheInfo.version ?? "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="运行模式">
            {{ cacheInfo.mode ?? "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="运行时长">
            {{ formatUptime(cacheInfo.uptimeSeconds) }}
          </el-descriptions-item>
          <el-descriptions-item label="已用内存">
            {{ cacheInfo.usedMemory ?? "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="内存峰值">
            {{ cacheInfo.usedMemoryPeak ?? "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="连接客户端数">
            {{ cacheInfo.clients ?? "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="当前库键总数">
            {{ cacheInfo.keyCount ?? "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="命中率">
            {{ cacheInfo.hitRate != null ? `${cacheInfo.hitRate}%` : "-" }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="font-bold mt-4 mb-2">命令调用统计（Top10）</div>
        <el-table :data="cacheInfo.commandStats" border stripe>
          <el-table-column label="命令" prop="name" min-width="120" />
          <el-table-column label="调用次数" prop="calls" min-width="120" />
          <el-table-column
            label="累计耗时（微秒）"
            prop="usec"
            min-width="160"
          />
        </el-table>
      </template>
    </el-card>
  </div>
</template>
