<script setup lang="ts">
import { ref, computed } from "vue";
import ReCol from "@/components/ReCol";
import { dirFormRules, menuFormRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { IconSelect } from "@/components/ReIcon";
import Segmented from "@/components/ReSegmented";
import ReAnimateSelector from "@/components/ReAnimateSelector";
import {
  menuTypeOptions,
  showLinkOptions,
  fixedTagOptions,
  keepAliveOptions,
  hiddenTagOptions,
  showParentOptions,
  frameLoadingOptions
} from "./utils/enums";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    menuType: 0,
    higherMenuOptions: [],
    parentId: 0,
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
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);

/**
 * 校验规则按菜单类型切换：
 * 目录（menuType=0）不需要组件路径，页面（menuType=1）才需要。
 * 组件路径用 v-show 隐藏但仍会参与校验，因此必须在规则层面区分，
 * 否则目录类型提交会被「组件路径为必填项」拦下。
 */
const rules = computed(() =>
  newFormInline.value.menuType === 1 ? menuFormRules : dirFormRules
);

function getRef() {
  return ruleFormRef.value;
}

defineExpose({ getRef });
</script>

<template>
  <el-form
    ref="ruleFormRef"
    :model="newFormInline"
    :rules="rules"
    label-width="82px"
  >
    <el-row :gutter="30">
      <!-- 分组：基础信息 -->
      <re-col :value="24" :xs="24" :sm="24">
        <div class="form-section-title form-section-title--top">基础信息</div>
      </re-col>

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
        <el-form-item label="菜单名称" prop="meta.title">
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

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="路由路径" prop="path">
          <el-input
            v-model="newFormInline.path"
            clearable
            placeholder="请输入路由路径"
          />
        </el-form-item>
      </re-col>
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

      <!-- 分组：高级设置（meta 元数据） -->
      <re-col :value="24" :xs="24" :sm="24">
        <div class="form-section-title">高级设置</div>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="菜单图标">
          <IconSelect v-model="newFormInline.meta.icon" class="w-full" />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="SVG图标">
          <el-input
            v-model="newFormInline.meta.rSvgName"
            clearable
            placeholder="remix icon SVG名称"
          />
        </el-form-item>
      </re-col>

      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
        <el-form-item label="进场动画">
          <ReAnimateSelector
            v-model="newFormInline.meta.transitionEnter"
            placeholder="请选择页面进场加载动画"
          />
        </el-form-item>
      </re-col>
      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
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
        v-show="newFormInline.menuType === 0"
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
        v-show="newFormInline.menuType === 0"
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

      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
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

      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
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
      <re-col
        v-show="newFormInline.menuType === 0"
        :value="12"
        :xs="24"
        :sm="24"
      >
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
    </el-row>
  </el-form>
</template>
