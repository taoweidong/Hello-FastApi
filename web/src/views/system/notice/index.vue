<script setup lang="ts">
import { ref } from "vue";
import { useNotice } from "./hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "Notice"
});

const tableRef = ref();
const formRef = ref();
const {
  loading,
  form,
  columns,
  dataList,
  pagination,
  totalPage,
  selectedIds,
  typeOptions,
  onSearch,
  resetForm,
  openDialog,
  handleDelete,
  handleBatchDelete,
  handleSelectionChange,
  handleSizeChange,
  handleCurrentChange
} = useNotice();

function onFullscreen() {
  tableRef.value.setAdaptive();
}
</script>

<template>
  <div class="main">
    <el-form
      ref="formRef"
      :inline="true"
      :model="form"
      class="search-form bg-bg_color w-full pl-8 pt-3 overflow-auto"
    >
      <el-form-item label="公告标题" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入公告标题"
          clearable
          class="w-45!"
        />
      </el-form-item>
      <el-form-item label="公告类型" prop="noticeType">
        <el-select
          v-model="form.noticeType"
          placeholder="请选择公告类型"
          clearable
          class="w-40!"
        >
          <el-option
            v-for="item in typeOptions()"
            :key="item.value"
            :label="item.label"
            :value="Number(item.value)"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="状态" prop="isActive">
        <el-select
          v-model="form.isActive"
          placeholder="请选择状态"
          clearable
          class="w-40!"
        >
          <el-option label="正常" :value="1" />
          <el-option label="关闭" :value="0" />
        </el-select>
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

    <PureTableBar
      title="通知公告管理"
      :columns="columns"
      :tableRef="tableRef?.getTableRef()"
      @refresh="onSearch"
      @fullscreen="onFullscreen"
    >
      <template #buttons>
        <el-button
          v-auth="'notice:add'"
          type="primary"
          :icon="useRenderIcon(AddFill)"
          @click="openDialog()"
        >
          发布公告
        </el-button>
        <el-popconfirm
          :title="`是否确认删除选中的 ${selectedIds.length} 条公告？`"
          @confirm="handleBatchDelete"
        >
          <template #reference>
            <el-button
              v-auth="'notice:delete'"
              type="danger"
              :icon="useRenderIcon(Delete)"
            >
              批量删除
            </el-button>
          </template>
        </el-popconfirm>
      </template>
      <template v-slot="{ size, dynamicColumns }">
        <pure-table
          ref="tableRef"
          adaptive
          :adaptiveConfig="{ offsetBottom: 45 }"
          align-whole="center"
          row-key="id"
          showOverflowTooltip
          table-layout="auto"
          :loading="loading"
          :size="size"
          :data="dataList"
          :columns="dynamicColumns"
          :pagination="{
            total: totalPage,
            pageSize: pagination.pageSize,
            currentPage: pagination.currentPage,
            size,
            background: true
          }"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @selection-change="handleSelectionChange"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        >
          <template #operation="{ row }">
            <el-button
              v-auth="'notice:edit'"
              class="reset-margin"
              link
              type="primary"
              :size="size"
              :icon="useRenderIcon(EditPen)"
              @click="openDialog('修改', row)"
            >
              修改
            </el-button>
            <el-popconfirm
              :title="`是否确认删除公告【${row.title}】`"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
                  v-auth="'notice:delete'"
                  class="reset-margin"
                  link
                  type="primary"
                  :size="size"
                  :icon="useRenderIcon(Delete)"
                >
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </pure-table>
      </template>
    </PureTableBar>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}

.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
</style>

<style lang="scss">
/* 公告详情弹窗（渲染于 body 层，需全局样式） */
.notice-detail {
  &-meta {
    display: flex;
    gap: 16px;
    align-items: center;
    margin-bottom: 16px;
    color: var(--el-text-color-secondary);
    font-size: 13px;
  }

  &-content {
    white-space: pre-wrap;
    line-height: 1.8;
  }
}
</style>
