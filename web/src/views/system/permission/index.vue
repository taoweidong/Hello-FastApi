<script setup lang="ts">
import { usePermission } from "./hook";
import { PureTableBar } from "@/components/RePureTableBar";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";

import Refresh from "~icons/ep/refresh";

defineOptions({
  name: "SystemPermission"
});

const {
  loading,
  menuLoading,
  saveLoading,
  roleList,
  menuTree,
  currentRoleId,
  treeRef,
  roleColumns,
  fetchRoleList,
  selectRole,
  handleSave
} = usePermission();
</script>

<template>
  <div class="main">
    <div class="flex gap-4 w-full">
      <!-- 左侧角色列表 -->
      <div class="w-1/3 min-w-75">
        <PureTableBar
          title="角色列表"
          :columns="roleColumns"
          @refresh="fetchRoleList"
        >
          <template v-slot="{ size, dynamicColumns }">
            <pure-table
              adaptive
              :adaptiveConfig="{ offsetBottom: 80 }"
              align-whole="center"
              row-key="id"
              table-layout="auto"
              :loading="loading"
              :size="size"
              :data="roleList"
              :columns="dynamicColumns"
              :header-cell-style="{
                background: 'var(--el-fill-color-light)',
                color: 'var(--el-text-color-primary)'
              }"
              highlight-current-row
              @current-change="selectRole"
            >
              <template #operation="{ row }">
                <el-button
                  link
                  type="primary"
                  :size="size"
                  :disabled="currentRoleId === row.id"
                  @click="selectRole(row)"
                >
                  {{ currentRoleId === row.id ? "已选择" : "配置权限" }}
                </el-button>
              </template>
            </pure-table>
          </template>
        </PureTableBar>
      </div>

      <!-- 右侧菜单权限树 -->
      <div class="flex-1">
        <PureTableBar
          :title="currentRoleId ? '菜单权限配置' : '请先选择角色'"
          @refresh="handleSave"
        >
          <template #buttons>
            <el-button
              type="primary"
              :loading="saveLoading"
              :disabled="!currentRoleId"
              @click="handleSave"
            >
              保存权限
            </el-button>
          </template>
          <template v-slot>
            <div class="p-4">
              <el-empty
                v-if="!currentRoleId"
                description="请在左侧选择一个角色"
              />
              <el-tree
                v-else
                ref="treeRef"
                :data="menuTree"
                :props="{ label: 'label', children: 'children' }"
                node-key="id"
                show-checkbox
                default-expand-all
                :loading="menuLoading"
                class="w-full"
              >
                <template #default="{ node, data }">
                  <span class="flex items-center gap-2">
                    <span>{{ node.label }}</span>
                    <el-tag v-if="data.menuType === 0" size="small" type="info">
                      目录
                    </el-tag>
                    <el-tag
                      v-else-if="data.menuType === 1"
                      size="small"
                      type="success"
                    >
                      页面
                    </el-tag>
                    <el-tag
                      v-else-if="data.menuType === 2"
                      size="small"
                      type="warning"
                    >
                      权限
                    </el-tag>
                  </span>
                </template>
              </el-tree>
            </div>
          </template>
        </PureTableBar>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
:deep(.el-tree-node__content) {
  height: 36px;
}
</style>
