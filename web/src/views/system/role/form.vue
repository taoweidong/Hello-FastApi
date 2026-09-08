<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    name: "",
    code: "",
    isActive: 1,
    dataScope: 1,
    description: ""
  })
});

const ruleFormRef = ref();
const newFormInline = ref(props.formInline);

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
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="角色名称" prop="name">
          <el-input
            v-model="newFormInline.name"
            clearable
            placeholder="请输入角色名称"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="角色标识" prop="code">
          <el-input
            v-model="newFormInline.code"
            clearable
            placeholder="请输入角色标识"
          />
        </el-form-item>
      </re-col>

      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="状态">
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

      <re-col>
        <el-form-item label="数据权限" prop="dataScope">
          <el-radio-group v-model="newFormInline.dataScope">
            <el-radio :value="1">全部数据权限</el-radio>
            <el-radio :value="2">自定义数据权限</el-radio>
            <el-radio :value="3">本部门数据权限</el-radio>
            <el-radio :value="4">本部门及以下数据权限</el-radio>
            <el-radio :value="5">仅本人数据权限</el-radio>
          </el-radio-group>
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
