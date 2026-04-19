<script setup lang="ts">
import { ref, watch, getCurrentInstance } from "vue";
import { useDictionary } from "./utils/hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "SystemDictionary"
});

const formRef = ref();
const tableRef = ref();
const treeRef = ref();

const {
  loading,
  treeLoading,
  treeSearchValue,
  columns,
  dictTypeList,
  selectedDictType,
  childDataList,
  onSearch,
  handleNodeClick,
  openAddDictType,
  openAddDictDetail,
  openAddDictDetailForNode,
  openDialog,
  handleDelete,
  handleDeleteType
} = useDictionary();

const { proxy } = getCurrentInstance();

/** 树过滤方法 */
const filterNode = (value: string, data: any) => {
  if (!value) return true;
  const searchText = `${data.name}(${data.value || data.label})`;
  return searchText.includes(value);
};

/** 监听搜索框变化 */
watch(treeSearchValue, val => {
  treeRef.value?.filter(val);
});

function onFullscreen() {
  tableRef.value.setAdaptive();
}
</script>

<template>
  <div class="main">
    <div class="flex w-full">
      <!-- 左侧面板：字典类型树 -->
      <div
        v-loading="treeLoading"
        class="w-70! shrink-0 mr-2 bg-bg_color overflow-hidden relative"
        :style="{ minHeight: `calc(100vh - 141px)` }"
      >
        <div class="flex items-center h-8.5 px-2">
          <el-input
            v-model="treeSearchValue"
            size="small"
            placeholder="请输入字典名称"
            clearable
          >
            <template #suffix>
              <el-icon class="el-input__icon">
                <IconifyIconOffline
                  v-show="treeSearchValue.length === 0"
                  icon="ri/search-line"
                />
              </el-icon>
            </template>
          </el-input>
        </div>
        <el-divider style="margin: 0" />
        <el-scrollbar height="calc(100vh - 210px)">
          <el-tree
            ref="treeRef"
            :data="dictTypeList"
            node-key="id"
            size="small"
            :props="{ children: 'children', label: 'name' }"
            default-expand-all
            :expand-on-click-node="false"
            :filter-node-method="filterNode"
            :highlight-current="true"
            @node-click="handleNodeClick"
          >
            <template #default="{ data }">
              <div
                class="rounded-sm flex items-center select-none hover:text-primary w-full"
                :style="{
                  color:
                    selectedDictType?.id === data.id
                      ? 'var(--el-color-primary)'
                      : '',
                  background:
                    selectedDictType?.id === data.id
                      ? 'var(--el-color-primary-light-9)'
                      : 'transparent'
                }"
              >
                <span class="truncate flex-1" :title="data.name">
                  {{ data.name }}
                  <span v-if="data.value" class="text-xs text-gray-400 ml-1">
                    ({{ data.value }})
                  </span>
                </span>
                <!-- 右键菜单按钮 -->
                <el-dropdown
                  class="mr-1"
                  :hide-on-click="false"
                  trigger="click"
                >
                  <el-icon class="cursor-pointer hover:text-primary">
                    <IconifyIconOffline icon="ri/more-2-fill" width="14" />
                  </el-icon>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item>
                        <el-button
                          class="reset-margin"
                          link
                          type="primary"
                          :icon="useRenderIcon(EditPen)"
                          @click="openDialog('修改', data)"
                        >
                          修改
                        </el-button>
                      </el-dropdown-item>
                      <el-dropdown-item>
                        <el-button
                          class="reset-margin"
                          link
                          type="primary"
                          :icon="useRenderIcon(AddFill)"
                          @click="openAddDictDetailForNode(data)"
                        >
                          新增子项
                        </el-button>
                      </el-dropdown-item>
                      <el-dropdown-item>
                        <el-button
                          class="reset-margin"
                          link
                          type="danger"
                          :icon="useRenderIcon(Delete)"
                          @click="handleDeleteType(data)"
                        >
                          删除
                        </el-button>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-tree>
        </el-scrollbar>
        <el-divider style="margin: 0" />
        <div class="p-2">
          <el-button
            type="primary"
            class="w-full"
            :icon="useRenderIcon(AddFill)"
            @click="openAddDictType"
          >
            新增子典
          </el-button>
        </div>
      </div>

      <!-- 右侧面板：字典详情表 -->
      <div class="flex-1">
        <PureTableBar
          title="字典管理（左侧字典树可通过右键单击进行修改和删除）"
          :columns="columns"
          :tableRef="tableRef?.getTableRef()"
          @refresh="onSearch"
          @fullscreen="onFullscreen"
        >
          <template #buttons>
            <el-button
              type="primary"
              plain
              :icon="useRenderIcon(AddFill)"
              @click="openAddDictDetail"
            >
              新增字典详情
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
              :data="childDataList"
              :columns="dynamicColumns"
              :header-cell-style="{
                background: 'var(--el-fill-color-light)',
                color: 'var(--el-text-color-primary)'
              }"
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
                  :title="`是否确认删除字典标签为${row.label}的这条数据`"
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
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-table__inner-wrapper::before) {
  height: 0;
}

:deep(.el-tree) {
  --el-tree-node-hover-bg-color: transparent;
}

:deep(.el-divider) {
  margin: 0;
}
</style>
