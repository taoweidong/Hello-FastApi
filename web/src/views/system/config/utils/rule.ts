import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
  key: [{ required: true, message: "配置键为必填项", trigger: "blur" }]
});
