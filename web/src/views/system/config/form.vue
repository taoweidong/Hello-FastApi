<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { usePublicHooks } from "@/views/system/hooks";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    id: "",
    key: "",
    value: "",
    access: 0,
    isActive: 1,
    inherit: 0,
    description: ""
  })
});

const ruleFormRef = ref();
const { switchStyle } = usePublicHooks();
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
        <el-form-item label="配置键" prop="key">
          <el-input
            v-model="newFormInline.key"
            clearable
            placeholder="请输入配置键"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="访问级别">
          <el-input-number
            v-model="newFormInline.access"
            class="w-full!"
            :min="0"
            :max="999"
            controls-position="right"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item label="配置值">
          <el-input
            v-model="newFormInline.value"
            placeholder="请输入配置值(JSON格式)"
            type="textarea"
            :rows="3"
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
            :style="switchStyle"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="是否继承">
          <el-switch
            v-model="newFormInline.inherit"
            :active-value="1"
            :inactive-value="0"
            inline-prompt
            active-text="是"
            inactive-text="否"
            :style="switchStyle"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item label="描述">
          <el-input
            v-model="newFormInline.description"
            placeholder="请输入描述"
            type="textarea"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
