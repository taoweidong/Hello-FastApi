<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { usePublicHooks } from "@/views/system/hooks";
import { IPRuleTypeChoices } from "@/views/system/constants";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    id: "",
    ipAddress: "",
    ruleType: "blacklist",
    reason: "",
    isActive: 1,
    expiresAt: "",
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
        <el-form-item label="IP地址" prop="ipAddress">
          <el-input
            v-model="newFormInline.ipAddress"
            clearable
            placeholder="请输入IP地址"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="规则类型">
          <el-select
            v-model="newFormInline.ruleType"
            placeholder="请选择规则类型"
            class="w-full!"
          >
            <el-option
              v-for="item in IPRuleTypeChoices"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
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
            :style="switchStyle"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="过期时间">
          <el-date-picker
            v-model="newFormInline.expiresAt"
            type="datetime"
            placeholder="留空则永不过期"
            value-format="YYYY-MM-DDTHH:mm:ss"
            class="w-full!"
          />
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item label="原因">
          <el-input
            v-model="newFormInline.reason"
            placeholder="请输入原因"
            type="textarea"
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
