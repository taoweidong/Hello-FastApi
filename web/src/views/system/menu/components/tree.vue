<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { handleTree } from "@/utils/tree";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import { isAllEmpty } from "@pureadmin/utils";

import ExpandIcon from "~icons/ep/arrow-down";
import CollapseIcon from "~icons/ep/arrow-up";

const props = defineProps<{
  treeData: Array<any>;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (e: "select", node: any): void;
  (e: "search", keyword: string): void;
}>();

const treeRef = ref();
const searchValue = ref("");
const isExpandAll = ref(true);

/** 过滤掉 menuType===2 的权限节点 */
const filteredTreeData = computed(() => {
  function filterNodes(nodes: Array<any>): Array<any> {
    return nodes
      .filter(node => node.menuType !== 2)
      .map(node => ({
        ...node,
        children: node.children ? filterNodes(node.children) : []
      }));
  }
  return filterNodes(props.treeData);
});

/** 搜索过滤 */
function filterMethod(query: string, node: any) {
  return (
    (node.meta?.title ?? node.name)?.includes(query) ||
    node.name?.includes(query)
  );
}

function onQueryChanged(query: string) {
  treeRef.value?.filter(query);
  emit("search", query);
}

/** 展开/折叠全部 */
function toggleExpandAll() {
  isExpandAll.value = !isExpandAll.value;
  const tree = treeRef.value;
  if (!tree) return;
  const nodes = tree.store._getAllNodes();
  nodes.forEach(node => {
    node.expanded = isExpandAll.value;
  });
}

/** 选中节点 */
function handleNodeClick(data: any) {
  emit("select", data);
}

defineExpose({ treeRef });
</script>

<template>
  <div class="menu-tree-container">
    <div class="flex items-center mb-3">
      <el-input
        v-model="searchValue"
        class="mr-2"
        placeholder="搜索菜单名称"
        clearable
        @input="onQueryChanged"
      />
      <el-button
        :icon="
          isExpandAll ? useRenderIcon(CollapseIcon) : useRenderIcon(ExpandIcon)
        "
        @click="toggleExpandAll"
      />
    </div>
    <el-tree
      ref="treeRef"
      v-loading="loading"
      :data="filteredTreeData"
      node-key="id"
      :props="{
        label: data => data.meta?.title ?? data.name,
        children: 'children',
        isLeaf: data => !data.children || data.children.length === 0
      }"
      highlight-current
      default-expand-all
      :expand-on-click-node="false"
      :filter-node-method="filterMethod"
      @node-click="handleNodeClick"
    >
      <template #default="{ data }">
        <span class="custom-tree-node">
          <span class="inline-block mr-1">
            <el-icon v-if="data.meta?.icon" size="16">
              <component :is="useRenderIcon(data.meta.icon)" />
            </el-icon>
          </span>
          <span>{{ data.meta?.title ?? data.name }}</span>
          <el-tag
            size="small"
            class="ml-2"
            :type="
              data.menuType === 0
                ? 'primary'
                : 'warning'
            "
            effect="plain"
          >
            {{
              data.menuType === 0
                ? "目录"
                : "页面"
            }}
          </el-tag>
        </span>
      </template>
    </el-tree>
  </div>
</template>

<style lang="scss" scoped>
.menu-tree-container {
  height: 100%;
  overflow: auto;
}

.custom-tree-node {
  display: flex;
  align-items: center;
  padding-right: 8px;
  font-size: 14px;
}
</style>
