<script setup lang="ts">
import dayjs from "dayjs";
import { getMineLogs } from "@/api/user";
import { reactive, ref, onMounted } from "vue";
import { deviceDetection } from "@pureadmin/utils";
import { message } from "@/utils/message";
import type { PaginationProps } from "@pureadmin/table";

defineOptions({
  name: "SecurityLog"
});

const loading = ref(true);
const dataList = ref([]);
const pagination = reactive<PaginationProps>({
  total: 0,
  pageSize: 10,
  currentPage: 1,
  background: true,
  layout: "prev, pager, next"
});
const columns: TableColumnList = [
  {
    label: "登录状态",
    prop: "status",
    minWidth: 100,
    formatter: ({ status }) => (status === 1 ? "登录成功" : "登录失败")
  },
  {
    label: "IP 地址",
    prop: "ip",
    minWidth: 140
  },
  {
    label: "操作系统",
    prop: "system",
    minWidth: 100
  },
  {
    label: "浏览器类型",
    prop: "browser",
    minWidth: 100
  },
  {
    label: "时间",
    prop: "loginTime",
    minWidth: 180,
    formatter: ({ loginTime }) =>
      loginTime ? dayjs(loginTime).format("YYYY-MM-DD HH:mm:ss") : "-"
  }
];

async function onSearch() {
  loading.value = true;
  try {
    const { code, data } = await getMineLogs({
      pageNum: pagination.currentPage,
      pageSize: pagination.pageSize
    });
    if (code === 0) {
      dataList.value = data.list;
      pagination.total = data.total;
      pagination.pageSize = data.pageSize;
      pagination.currentPage = data.currentPage;
    }
  } catch {
    message("安全日志加载失败", { type: "error" });
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  onSearch();
});

function handleSizeChange(val: number) {
  pagination.pageSize = val;
  onSearch();
}

function handleCurrentChange(val: number) {
  pagination.currentPage = val;
  onSearch();
}
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">安全日志</h3>
    <pure-table
      row-key="id"
      showOverflowTooltip
      table-layout="auto"
      :loading="loading"
      :data="dataList"
      :columns="columns"
      :pagination="pagination"
      @page-size-change="handleSizeChange"
      @page-current-change="handleCurrentChange"
    />
  </div>
</template>
