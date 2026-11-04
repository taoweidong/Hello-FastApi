<script setup lang="ts">
import dayjs from "dayjs";
import { useI18n } from "vue-i18n";
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { noticesData } from "./data";
import type { ListItem } from "./data";
import NoticeList from "./components/NoticeList.vue";
import { noticeApi } from "@/api/system/notice";
import { realtime } from "@/utils/websocket";
import { message } from "@/utils/message";

import BellIcon from "~icons/ri/notification-3-line";
import ArrowRightIcon from "~icons/ri/arrow-right-s-line";

const { t } = useI18n();
const dropdownRef = ref();
const notices = ref(noticesData);
const activeKey = ref(noticesData[0]?.key);
/** 铃铛摇晃动画开关（收到实时通知时触发一次） */
const bellRing = ref(false);

/** 后端公告 DTO → 列表项归一化（历史拉取与实时推送共用） */
function toItem(n: any): ListItem {
  return {
    id: n.id,
    avatar: "",
    title: n.title,
    description: n.content || "",
    datetime: n.createdTime
      ? dayjs(n.createdTime).format("YYYY-MM-DD HH:mm")
      : "",
    type: String(n.noticeType)
  };
}

/** 从后端拉取最新启用公告填充铃铛下拉（公告→tab1，通知→tab2），历史兜底 */
async function fetchNotices() {
  try {
    const { code, data } = await noticeApi.latest();
    if (code !== 0 || !Array.isArray(data)) return;
    const announceTab = notices.value.find(item => item.key === "1");
    const noticeTab = notices.value.find(item => item.key === "2");
    if (announceTab) {
      announceTab.list = data.filter(n => n.noticeType === 2).map(toItem);
    }
    if (noticeTab) {
      noticeTab.list = data.filter(n => n.noticeType === 1).map(toItem);
    }
  } catch {
    // 铃铛取数失败静默降级，不影响布局
  }
}

/** 实时推送回调：将新公告插入对应 tab 顶部 + 弹窗提示 + 铃铛摇晃 */
function onRealtimeNotice(payload: any) {
  if (!payload) return;
  const key = payload.noticeType === 2 ? "1" : "2";
  const tab = notices.value.find(item => item.key === key);
  if (tab) {
    tab.list.unshift(toItem(payload));
  }
  const label = payload.noticeType === 2 ? "公告" : "通知";
  message(`${label}：${payload.title ?? ""}`, { type: "warning" });
  // 触发一次摇晃动画：先 false 再 true 以重新触发 CSS 动画
  bellRing.value = false;
  requestAnimationFrame(() => {
    bellRing.value = true;
    window.setTimeout(() => (bellRing.value = false), 1000);
  });
}

onMounted(() => {
  fetchNotices();
  realtime.on("notice", onRealtimeNotice);
});

onBeforeUnmount(() => {
  realtime.off("notice", onRealtimeNotice);
});

const getLabel = computed(
  () => item =>
    t(item.name) + (item.list.length > 0 ? `(${item.list.length})` : "")
);

const currentNoticeHasData = computed(() => {
  const currentNotice = notices.value.find(
    item => item.key === activeKey.value
  );
  return currentNotice && currentNotice.list.length > 0;
});

const hasAnyNoticeData = computed(() => {
  return notices.value.some(
    item => Array.isArray(item.list) && item.list.length > 0
  );
});

const onWatchMore = () => {
  dropdownRef.value.handleClose();
};

const onMarkAsRead = () => {
  const currentNotice = notices.value.find(
    item => item.key === activeKey.value
  );
  if (currentNotice) {
    currentNotice.list = [];
  }
};
</script>

<template>
  <el-dropdown ref="dropdownRef" trigger="click" placement="bottom-end">
    <span
      :class="['dropdown-badge', 'navbar-bg-hover', 'select-none', 'mr-1.75']"
    >
      <el-badge is-dot :hidden="!hasAnyNoticeData">
        <span class="header-notice-icon" :class="{ 'bell-ring': bellRing }">
          <IconifyIconOffline :icon="BellIcon" />
        </span>
      </el-badge>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-tabs
          v-model="activeKey"
          :stretch="true"
          class="dropdown-tabs"
          :style="{ width: notices.length === 0 ? '200px' : '330px' }"
        >
          <el-empty
            v-if="notices.length === 0"
            :description="t('status.pureNoMessage')"
            :image-size="60"
          />
          <span v-else>
            <template v-for="item in notices" :key="item.key">
              <el-tab-pane :label="getLabel(item)" :name="`${item.key}`">
                <el-scrollbar max-height="345px">
                  <div class="noticeList-container">
                    <NoticeList :list="item.list" :emptyText="item.emptyText" />
                  </div>
                </el-scrollbar>
              </el-tab-pane>
            </template>
          </span>
        </el-tabs>
        <div
          v-if="currentNoticeHasData"
          class="border-t border-t-(--el-border-color-light) text-sm"
        >
          <div class="flex-bc m-1">
            <el-button type="primary" size="small" text @click="onWatchMore">
              {{ t("buttons.pureWatchMore") }}
              <IconifyIconOffline :icon="ArrowRightIcon" />
            </el-button>
            <el-button type="primary" size="small" text @click="onMarkAsRead">
              {{ t("buttons.pureMarkAsRead") }}
            </el-button>
          </div>
        </div>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<style lang="scss" scoped>
/* ”铃铛“摇晃衰减动画 */
@keyframes pure-bell-ring {
  0%,
  100% {
    transform-origin: top;
  }

  15% {
    transform: rotateZ(10deg);
  }

  30% {
    transform: rotateZ(-10deg);
  }

  45% {
    transform: rotateZ(5deg);
  }

  60% {
    transform: rotateZ(-5deg);
  }

  75% {
    transform: rotateZ(2deg);
  }
}

.dropdown-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 48px;
  cursor: pointer;

  .header-notice-icon {
    font-size: 16px;
  }

  /* 收到实时通知时的摇晃动画 */
  .header-notice-icon.bell-ring svg {
    animation: pure-bell-ring 1s both;
  }

  &:hover {
    .header-notice-icon svg {
      animation: pure-bell-ring 1s both;
    }
  }
}

.dropdown-tabs {
  .noticeList-container {
    padding: 15px 24px 0;
  }

  :deep(.el-tabs__header) {
    margin: 0;
  }

  :deep(.el-tabs__nav-wrap)::after {
    height: 1px;
  }

  :deep(.el-tabs__nav-wrap) {
    padding: 0 36px;
  }
}
</style>
