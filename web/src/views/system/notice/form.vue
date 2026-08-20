<script setup lang="ts">
import { ref } from "vue";
import ReCol from "@/components/ReCol";
import { formRules } from "./utils/rule";
import { FormProps } from "./utils/types";
import { useDict } from "@/composables/useDict";
import { usePublicHooks } from "@/views/system/hooks";

const props = withDefaults(defineProps<FormProps>(), {
  formInline: () => ({
    id: "",
    title: "",
    content: "",
    noticeType: 1,
    isActive: 1
  })
});

const ruleFormRef = ref();
const { switchStyle } = usePublicHooks();
const newFormInline = ref(props.formInline);

/** 公告类型字典（字典缺失时回退静态选项） */
const dicts = useDict("sys_notice_type");
const noticeTypeOptions = ref([
  { label: "通知", value: "1" },
  { label: "公告", value: "2" }
]);

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
        <el-form-item label="公告标题" prop="title">
          <el-input
            v-model="newFormInline.title"
            clearable
            placeholder="请输入公告标题"
          />
        </el-form-item>
      </re-col>
      <re-col :value="12" :xs="24" :sm="24">
        <el-form-item label="公告类型" prop="noticeType">
          <el-select
            v-model="newFormInline.noticeType"
            class="w-full!"
            placeholder="请选择公告类型"
          >
            <el-option
              v-for="item in dicts['sys_notice_type'].length > 0
                ? dicts['sys_notice_type']
                : noticeTypeOptions"
              :key="item.value"
              :label="item.label"
              :value="Number(item.value)"
            />
          </el-select>
        </el-form-item>
      </re-col>

      <re-col>
        <el-form-item label="公告内容">
          <el-input
            v-model="newFormInline.content"
            placeholder="请输入公告内容"
            type="textarea"
            :rows="4"
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
            active-text="正常"
            inactive-text="关闭"
            :style="switchStyle"
          />
        </el-form-item>
      </re-col>
    </el-row>
  </el-form>
</template>
