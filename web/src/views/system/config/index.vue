<script setup lang="ts">
import { ref } from "vue";
import { useConfig } from "./hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "SystemConfig"
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
  dialogVisible,
  dialogTitle,
  ruleForm,
  onSearch,
  resetForm,
  openDialog,
  handleSubmit,
  handleDelete,
  handleSizeChange,
  handleCurrentChange
} = useConfig();

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
      <el-form-item label="配置键" prop="key">
        <el-input
          v-model="form.key"
          placeholder="请输入配置键"
          clearable
          class="w-45!"
        />
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
      title="系统配置管理"
      :columns="columns"
      :tableRef="tableRef?.getTableRef()"
      @refresh="onSearch"
      @fullscreen="onFullscreen"
    >
      <template #buttons>
        <el-button
          type="primary"
          :icon="useRenderIcon(AddFill)"
          @click="openDialog()"
        >
          新增配置
        </el-button>
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
          :pagination="{ total: totalPage, pageSize: pagination.pageSize, currentPage: pagination.currentPage, size, background: true }"
          :header-cell-style="{
            background: 'var(--el-fill-color-light)',
            color: 'var(--el-text-color-primary)'
          }"
          @page-size-change="handleSizeChange"
          @page-current-change="handleCurrentChange"
        >
          <template #operation="{ row }">
            <el-button
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
              :title="`是否确认删除配置【${row.key}】`"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button
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

    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="500px"
      destroy-on-close
    >
      <el-form :model="ruleForm" label-width="82px">
        <el-form-item label="配置键" prop="key" required>
          <el-input v-model="ruleForm.key" placeholder="请输入配置键" clearable />
        </el-form-item>
        <el-form-item label="配置值" prop="value" required>
          <el-input
            v-model="ruleForm.value"
            placeholder="请输入配置值(JSON格式)"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="访问级别">
          <el-input-number v-model="ruleForm.access" :min="0" :max="999" controls-position="right" />
        </el-form-item>
        <el-form-item label="是否启用">
          <el-switch
            v-model="ruleForm.isActive"
            inline-prompt
            active-text="启用"
            inactive-text="停用"
          />
        </el-form-item>
        <el-form-item label="是否继承">
          <el-switch
            v-model="ruleForm.inherit"
            inline-prompt
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="ruleForm.description" placeholder="请输入描述" clearable />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
::deep(.el-table__inner-wrapper::before) {
  height: 0;
}
.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
</style>
