<script setup lang="ts">
import { ref, computed } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { usePublicHooks } from "@/views/system/hooks";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    higherDictOptions: [],
    parentId: 0,
    name: "",
    label: "",
    value: "",
    sort: null,
    isActive: 1,
    description: ""
  })
});

const ruleFormRef = ref();
const { switchStyle } = usePublicHooks();
const newFormInline = ref(props.formInline);

/** 是否为根级字典类型（新增子典时 parentId 为 0 或空） */
const isRootType = computed(() => {
  return (
    !newFormInline.value.parentId ||
    newFormInline.value.parentId === 0 ||
    newFormInline.value.parentId === "0"
  );
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
    :rules="formRules"
    label-width="82px"
  >
    <el-row :gutter="30">
      <!-- 根级字典类型才显示字典名称（必填） -->
      <re-col v-if="isRootType" :value="12" :xs="24" :sm="24">
        <el-form-item label="字典名称" prop="name">
          <el-input
            v-model="newFormInline.name"
            clearable
            placeholder="请输入字典名称"
          />
        </el-form-item>
      </re-col>

      <!-- 子项详情时显示所属字典（只读） -->
      <re-col v-if="!isRootType" :value="24" :xs="24" :sm="24">
        <el-form-item label="所属字典">
          <el-input
            v-model="newFormInline.name"
            disabled
            placeholder="所属字典"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="显示标签" :prop="isRootType ? '' : 'label'">
          <el-input
            v-model="newFormInline.label"
            clearable
            placeholder="请输入显示标签"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="字典值">
          <el-input
            v-model="newFormInline.value"
            clearable
            placeholder="请输入字典值"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="排序">
          <el-input-number
            v-model="newFormInline.sort"
            class="w-full!"
            :min="0"
            :max="9999"
            controls-position="right"
            placeholder="不填自动递增"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="字典状态">
          <el-switch
            v-model="newFormInline.isActive"
            :active-value="1"
            :inactive-value="0"
            inline-prompt
            active-text="启用"
            inactive-text="停用"
            :style="switchStyle"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item label="描述">
          <el-input
            v-model="newFormInline.description"
            placeholder="请输入描述信息"
            type="textarea"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
