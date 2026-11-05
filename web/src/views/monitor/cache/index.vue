<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import {
  clearAllCache,
  clearCacheGroup,
  getCacheGroups,
  getCacheInfo,
  type CacheGroup,
  type CacheInfo
} from "@/api/system/monitor";
import { message } from "@/utils/message";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import Refresh from "~icons/ep/refresh";

defineOptions({
  name: "CacheMonitor"
});

const loading = ref(false);
const groupsLoading = ref(false);
const clearLoading = ref(false);
const cacheInfo = ref<CacheInfo | null>(null);
const cacheGroups = ref<CacheGroup[]>([]);

/** 是否存在可清理的分组（决定"清空全部"按钮可用性） */
const hasClearableGroups = computed(() =>
  cacheGroups.value.some(g => g.clearable)
);

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

async function fetchGroups() {
  groupsLoading.value = true;
  try {
    const { data } = await getCacheGroups();
    cacheGroups.value = data ?? [];
  } catch {
    // 非管理员/网络异常时不打断页面：清单区留空
    cacheGroups.value = [];
  } finally {
    groupsLoading.value = false;
  }
}

/** 快速清理单个分组（后端强制管理员权限，令牌黑名单组不可清理） */
async function handleClearGroup(group: CacheGroup) {
  clearLoading.value = true;
  try {
    const { code, data } = await clearCacheGroup(group.key);
    if (code === 0) {
      message(`已清理「${group.name}」${data?.deleted ?? 0} 个缓存键`, {
        type: "success"
      });
      await Promise.all([fetchGroups(), fetchInfo()]);
    }
  } catch {
    message("清理失败：需要管理员权限或缓存服务不可用", { type: "error" });
  } finally {
    clearLoading.value = false;
  }
}

/** 清空全部可清理业务缓存（不含令牌黑名单与限流计数键） */
async function handleClearAll() {
  clearLoading.value = true;
  try {
    const { code, data } = await clearAllCache();
    if (code === 0) {
      message(`已清空全部业务缓存，共 ${data?.deleted ?? 0} 个缓存键`, {
        type: "success"
      });
      await Promise.all([fetchGroups(), fetchInfo()]);
    }
  } catch {
    message("清空失败：需要管理员权限或缓存服务不可用", { type: "error" });
  } finally {
    clearLoading.value = false;
  }
}

onMounted(() => {
  fetchInfo();
  fetchGroups();
});
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

    <!-- 缓存数据清单与清理（清理操作仅管理员：按钮按 monitor:manage 权限码显隐，后端再次校验） -->
    <el-card v-loading="groupsLoading" shadow="never" class="mt-4">
      <template #header>
        <div class="flex-bc">
          <span class="font-bold">缓存数据</span>
          <el-popconfirm
            v-if="hasClearableGroups"
            title="将清空全部可清理业务缓存（不含令牌黑名单与限流键），已登录用户需重新获取缓存，确认继续？"
            width="360"
            confirm-button-text="清空"
            cancel-button-text="取消"
            confirm-button-type="danger"
            @confirm="handleClearAll"
          >
            <template #reference>
              <el-button
                v-auth="'monitor:manage'"
                type="danger"
                plain
                :icon="useRenderIcon(Delete)"
                :loading="clearLoading"
              >
                清空全部缓存
              </el-button>
            </template>
          </el-popconfirm>
        </div>
      </template>

      <el-alert
        type="info"
        :closable="false"
        show-icon
        title="清理缓存后相关数据将回源数据库重建；令牌黑名单为安全数据不可清理。"
        class="mb-3"
      />

      <el-table :data="cacheGroups" border stripe>
        <el-table-column label="缓存分组" prop="name" min-width="140" />
        <el-table-column label="键前缀" prop="prefix" min-width="160">
          <template #default="{ row }">
            <code>{{ row.prefix }}*</code>
          </template>
        </el-table-column>
        <el-table-column
          label="键数量"
          prop="count"
          min-width="100"
          align="right"
        />
        <el-table-column label="操作" min-width="120" align="center">
          <template #default="{ row }">
            <el-popconfirm
              v-if="row.clearable"
              :title="`确认清理「${row.name}」的全部 ${row.count} 个缓存键？`"
              width="280"
              confirm-button-text="清理"
              cancel-button-text="取消"
              confirm-button-type="danger"
              @confirm="handleClearGroup(row as CacheGroup)"
            >
              <template #reference>
                <el-button
                  v-auth="'monitor:manage'"
                  type="danger"
                  text
                  size="small"
                  :icon="useRenderIcon(Delete)"
                  :loading="clearLoading"
                >
                  快速清理
                </el-button>
              </template>
            </el-popconfirm>
            <span v-else class="text-gray-400">安全数据，不可清理</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>
