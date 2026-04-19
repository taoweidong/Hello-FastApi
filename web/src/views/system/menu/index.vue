<script setup lang="ts">
import { ref, computed } from "vue";
import { useMenu } from "./utils/hook";
import { transformI18n } from "@/plugins/i18n";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import MenuTree from "./components/tree.vue";
import MenuEdit from "./components/edit.vue";

import Delete from "~icons/ep/delete";
import EditPen from "~icons/ep/edit-pen";
import Refresh from "~icons/ep/refresh";
import AddFill from "~icons/ri/add-circle-line";

defineOptions({
  name: "SystemMenu"
});

const formRef = ref();
const tableRef = ref();
const treeRef = ref();
const editFormRef = ref();

const {
  form,
  loading,
  columns,
  dataList,
  onSearch,
  resetForm,
  openDialog,
  handleDelete,
  handleSelectionChange
} = useMenu();

/** 是否使用左右分栏布局 */
const useSplitLayout = ref(true);
/** 当前选中的菜单节点 */
const selectedNode = ref<any>(null);
/** 是否显示编辑面板 */
const showEditPanel = ref(false);
/** 编辑面板标题 */
const editTitle = ref("新增菜单");
/** 编辑表单数据 */
const editFormData = ref<any>(null);

/** 点击树节点 — 选中并显示详情 */
function handleTreeSelect(node: any) {
  selectedNode.value = node;
}

/** 从树节点新增子菜单 */
function handleAddChild(parentNode?: any) {
  editTitle.value = "新增菜单";
  showEditPanel.value = true;
  editFormData.value = {
    menuType: 0,
    higherMenuOptions: [],
    parentId: parentNode?.id ?? 0,
    name: "",
    path: "",
    component: "",
    rank: 99,
    isActive: 1,
    meta: {
      title: "",
      icon: "",
      rSvgName: "",
      isShowMenu: true,
      isShowParent: false,
      isKeepalive: true,
      frameUrl: "",
      frameLoading: true,
      transitionEnter: "",
      transitionLeave: "",
      isHiddenTag: false,
      fixedTag: false,
      dynamicLevel: null
    }
  };
}

/** 编辑菜单 */
function handleEdit(row: any) {
  editTitle.value = "修改菜单";
  showEditPanel.value = true;
  editFormData.value = {
    ...row,
    meta: { ...row.meta }
  };
}

function onFullscreen() {
  tableRef.value?.setAdaptive?.();
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
      <el-form-item label="菜单名称：" prop="title">
        <el-input
          v-model="form.title"
          placeholder="请输入菜单名称"
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

    <div
      class="flex gap-4"
      style="height: calc(100vh - 260px); min-height: 400px"
    >
      <!-- 左侧：菜单树 -->
      <div class="w-1/4 min-w-64 bg-bg_color rounded-md p-4 overflow-auto">
        <div class="flex-bc mb-2">
          <span class="font-bold text-base">菜单结构</span>
          <el-button
            type="primary"
            size="small"
            :icon="useRenderIcon(AddFill)"
            @click="handleAddChild()"
          >
            新增
          </el-button>
        </div>
        <MenuTree
          ref="treeRef"
          :treeData="dataList"
          :loading="loading"
          @select="handleTreeSelect"
        />
      </div>

      <!-- 右侧：表格/编辑 -->
      <div class="flex-1 bg-bg_color rounded-md overflow-hidden">
        <PureTableBar
          title="菜单管理"
          :columns="columns"
          :isExpandAll="false"
          :tableRef="tableRef?.getTableRef()"
          @refresh="onSearch"
          @fullscreen="onFullscreen"
        >
          <template #buttons>
            <el-button
              type="primary"
              :icon="useRenderIcon(AddFill)"
              @click="handleAddChild()"
            >
              新增根菜单
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
              :header-cell-style="{
                background: 'var(--el-fill-color-light)',
                color: 'var(--el-text-color-primary)'
              }"
              @selection-change="handleSelectionChange"
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
                <el-button
                  class="reset-margin"
                  link
                  type="primary"
                  :size="size"
                  :icon="useRenderIcon(AddFill)"
                  @click="openDialog('新增', { parentId: row.id } as any)"
                >
                  新增
                </el-button>
                <el-popconfirm
                  :title="`是否确认删除菜单名称为${transformI18n(row.title)}的这条数据${row?.children?.length > 0 ? '。注意下级菜单也会一并删除，请谨慎操作' : ''}`"
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

.main-content {
  margin: 24px 24px 0 !important;
}

.search-form {
  :deep(.el-form-item) {
    margin-bottom: 12px;
  }
}
</style>
