<script setup lang="ts">
import { ref, computed, watch } from "vue";
import ReCol from "@/components/ReCol";
import { FormProps } from "../utils/types";
import { IconSelect } from "@/components/ReIcon";
import Segmented from "@/components/ReSegmented";
import ReAnimateSelector from "@/components/ReAnimateSelector";
import {
  dirFormRules,
  menuFormRules,
  permissionFormRules
} from "../utils/rule";
import {
  menuTypeOptions,
  showLinkOptions,
  fixedTagOptions,
  keepAliveOptions,
  hiddenTagOptions,
  showParentOptions,
  frameLoadingOptions,
  methodOptions
} from "../utils/enums";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    menuType: 0,
    higherMenuOptions: [],
    parentId: 0,
    name: "",
    path: "",
    component: "",
    rank: 99,
    method: "",
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
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);

/** 根据菜单类型动态切换校验规则 */
const currentFormRules = computed(() => {
  switch (newFormInline.value.menuType) {
    case 0:
      return dirFormRules;
    case 1:
      return menuFormRules;
    case 2:
      return permissionFormRules;
    default:
      return menuFormRules;
  }
});

function getRef() {
  return ruleFormRef.value;
}

defineExpose({ getRef });
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="newFormInline"
    :rules="currentFormRules"
    label-width="82px"
  >
    <el-row :gutter="30">
      <re-col>
        <el-form-item label="菜单类型">
          <Segmented
            v-model="newFormInline.menuType"
            :options="menuTypeOptions"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item label="上级菜单">
          <el-cascader
            v-model="newFormInline.parentId"
            class="w-full"
            :options="newFormInline.higherMenuOptions"
            :props="{
              value: 'id',
              label: 'title',
              emitPath: false,
              checkStrictly: true
            }"
            clearable
            filterable
            placeholder="请选择上级菜单"
          >
            <template #default="{ node, data }">
              <span>{{ data.meta?.title ?? data.title ?? data.name }}</span>
              <span v-if="!node.isLeaf">
                ({{ data.children?.length ?? 0 }})
              </span>
            </template>
          </el-cascader>
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="菜单名称" prop="title">
          <el-input
            v-model="newFormInline.meta.title"
            clearable
            placeholder="请输入菜单名称"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="路由名称" prop="name">
          <el-input
            v-model="newFormInline.name"
            clearable
            placeholder="请输入路由名称（唯一标识）"
          />
        </el-form-item>
      </re-col>

      <!-- 目录/页面类型：路由路径 -->
      <re-col v-if="newFormInline.menuType !== 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="路由路径" prop="path">
          <el-input
            v-model="newFormInline.path"
            clearable
            placeholder="请输入路由路径"
          />
        </el-form-item>
      </re-col>
      <!-- 页面类型：组件路径 -->
      <re-col
        v-show="newFormInline.menuType === 1"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="组件路径" prop="component">
          <el-input
            v-model="newFormInline.component"
            clearable
            placeholder="请输入组件路径"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="菜单排序">
          <el-input-number
            v-model="newFormInline.rank"
            class="w-full!"
            :min="1"
            :max="9999"
            controls-position="right"
          />
        </el-form-item>
      </re-col>

      <!-- 权限类型：HTTP方法选择 -->
      <re-col v-if="newFormInline.menuType === 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="请求方法" prop="method">
          <el-select
            v-model="newFormInline.method"
            placeholder="请选择HTTP方法"
            class="w-full"
          >
            <el-option
              v-for="opt in methodOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
      </re-col>

      <!-- 以下为 meta 元数据字段（仅目录/页面类型显示） -->
      <re-col
        v-show="newFormInline.menuType !== 2"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="菜单图标">
          <IconSelect v-model="newFormInline.meta.icon" class="w-full" />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType !== 2"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="SVG图标">
          <el-input
            v-model="newFormInline.meta.rSvgName"
            clearable
            placeholder="remix icon SVG名称"
          />
        </el-form-item>
      </re-col>

      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="进场动画">
          <ReAnimateSelector
            v-model="newFormInline.meta.transitionEnter"
            placeholder="请选择页面进场加载动画"
          />
        </el-form-item>
      </re-col>
      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="离场动画">
          <ReAnimateSelector
            v-model="newFormInline.meta.transitionLeave"
            placeholder="请选择页面离场加载动画"
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType === 1"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="iframe链接">
          <el-input
            v-model="newFormInline.meta.frameUrl"
            clearable
            placeholder="请输入 iframe 链接地址"
          />
        </el-form-item>
      </re-col>
      <re-col v-if="newFormInline.menuType === 1" :value="12" :xs="24" :sm="24">
        <el-form-item label="加载动画">
          <Segmented
            :modelValue="newFormInline.meta.frameLoading ? 0 : 1"
            :options="frameLoadingOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.meta.frameLoading = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType !== 2"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="是否显示">
          <Segmented
            :modelValue="newFormInline.meta.isShowMenu ? 0 : 1"
            :options="showLinkOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.meta.isShowMenu = value;
              }
            "
          />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType !== 2"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="父级菜单">
          <Segmented
            :modelValue="newFormInline.meta.isShowParent ? 0 : 1"
            :options="showParentOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.meta.isShowParent = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="缓存页面">
          <Segmented
            :modelValue="newFormInline.meta.isKeepalive ? 0 : 1"
            :options="keepAliveOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.meta.isKeepalive = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="标签页">
          <Segmented
            :modelValue="newFormInline.meta.isHiddenTag ? 1 : 0"
            :options="hiddenTagOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.meta.isHiddenTag = value;
              }
            "
          />
        </el-form-item>
      </re-col>
      <re-col v-show="newFormInline.menuType < 2" :value="12" :xs="24" :sm="24">
        <el-form-item label="固定标签页">
          <Segmented
            :modelValue="newFormInline.meta.fixedTag ? 0 : 1"
            :options="fixedTagOptions"
            @change="
              ({ option: { value } }) => {
                newFormInline.meta.fixedTag = value;
              }
            "
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="是否启用">
          <el-switch
            v-model="newFormInline.isActive"
            :active-value="1"
            :inactive-value="0"
            inline-prompt
            active-text="启用"
            inactive-text="停用"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
