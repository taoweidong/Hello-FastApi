import { reactive } from "vue";
import type { FormRules } from "element-plus";

/**
 * 字典类型（根级）表单校验规则
 * 根级只需填写字典名称，显示标签仅在字典详情（子项）形态下必填
 */
export const dictTypeRules = reactive(<FormRules>{
  name: [{ required: true, message: "字典名称为必填项", trigger: "blur" }]
});

/** 字典详情（子项）表单校验规则 */
export const dictItemRules = reactive(<FormRules>{
  label: [{ required: true, message: "显示标签为必填项", trigger: "blur" }]
});

/** 向后兼容：默认表单校验规则（同字典类型） */
export const formRules = dictTypeRules;
