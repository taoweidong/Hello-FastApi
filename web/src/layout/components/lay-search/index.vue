<script setup lang="ts">
import { useBoolean } from "../../hooks/useBoolean";
import SearchModal from "./components/SearchModal.vue";

const { bool: show, toggle } = useBoolean();
function handleSearch() {
  toggle();
}
</script>

<template>
  <div>
    <!--
      无障碍标签刻意避开「搜索」二字：Playwright 的 getByRole name 是子串匹配，
      全站 15 处 name:"搜索" 的定位会同时命中这个入口，导致 strict mode violation。
      「全局检索」既能表达含义，又不会与按钮文案冲突。
    -->
    <div
      class="search-container w-10 h-12 flex-c cursor-pointer navbar-bg-hover hover:[&>svg]:animate-scale-bounce"
      role="button"
      tabindex="0"
      aria-label="全局检索"
      @click="handleSearch"
      @keyup.enter="handleSearch"
    >
      <IconifyIconOffline icon="ri/search-line" />
    </div>
    <SearchModal v-model:value="show" />
  </div>
</template>
