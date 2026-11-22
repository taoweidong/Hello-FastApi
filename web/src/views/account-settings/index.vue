<script setup lang="ts">
import { getMine } from "@/api/user";
import { useRouter } from "vue-router";
import Profile from "./components/Profile.vue";
import { storeToRefs } from "pinia";
import { ref, onMounted, onBeforeMount } from "vue";
import Preferences from "./components/Preferences.vue";
import SecurityLog from "./components/SecurityLog.vue";
import AccountManagement from "./components/AccountManagement.vue";
import { useUserStoreHook } from "@/store/modules/user";
import { useGlobal } from "@pureadmin/utils";
import { useDataThemeChange } from "@/layout/hooks/useDataThemeChange";
import ReCol from "@/components/ReCol";

import leftLine from "~icons/ri/arrow-left-s-line";

defineOptions({
  name: "AccountSettings"
});

const router = useRouter();
const { $storage } = useGlobal<GlobalPropertiesApi>();
onBeforeMount(() => {
  useDataThemeChange().dataThemeChange($storage.layout?.themeMode);
});

/** 头部用户信息（/mine 接口回填） */
const userInfo = ref({
  avatar: "",
  username: "",
  nickname: ""
});
/** 角色标签：登录后已缓存于 user store，直接读取，不新增接口调用 */
const { roles } = storeToRefs(useUserStoreHook());

onMounted(async () => {
  const { code, data } = await getMine();
  if (code === 0) {
    userInfo.value = data;
  }
});
</script>

<template>
  <div class="h-full overflow-auto bg-(--el-bg-color-page) p-(--pure-space-4)">
    <!-- 头部用户信息区：头像 + 名称 + 角色标签 + 返回（颜色全部走 EP 变量，dark 自动适配） -->
    <el-card shadow="never" class="mb-(--pure-space-4)">
      <div
        class="flex flex-wrap items-center gap-x-(--pure-space-6) gap-y-(--pure-space-3)"
      >
        <el-avatar :size="64" :src="userInfo.avatar" />
        <div class="flex flex-col min-w-0">
          <span class="text-lg font-bold truncate">
            {{ userInfo.nickname || userInfo.username }}
          </span>
          <span
            class="text-sm mt-(--pure-space-1)"
            style="color: var(--el-text-color-secondary)"
          >
            {{ userInfo.username }}
          </span>
        </div>
        <div
          v-if="roles.length"
          class="flex flex-wrap items-center gap-(--pure-space-2)"
        >
          <el-tag v-for="role in roles" :key="role" effect="plain">
            {{ role }}
          </el-tag>
        </div>
        <div class="ml-auto">
          <el-button :icon="leftLine" @click="router.go(-1)">返回</el-button>
        </div>
      </div>
    </el-card>

    <!-- 分区卡片栅格：资料 / 账户安全 / 偏好 / 安全日志。
         四个功能组件保持原实现不变，仅改为卡片分区呈现；
         ≥992px 双列、以下单列堆叠（re-col 断点覆盖）。 -->
    <el-row :gutter="16">
      <re-col :value="12" :xs="24" :sm="24">
        <el-card shadow="never" class="mb-(--pure-space-4)">
          <Profile />
        </el-card>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-card shadow="never" class="mb-(--pure-space-4)">
          <AccountManagement />
        </el-card>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-card shadow="never" class="mb-(--pure-space-4)">
          <Preferences />
        </el-card>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-card shadow="never" class="mb-(--pure-space-4)">
          <SecurityLog />
        </el-card>
      </re-col>
    </el-row>
  </div>
</template>
