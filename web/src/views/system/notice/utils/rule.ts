import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 自定义表单规则校验 */
export const formRules = reactive(<FormRules>{
  title: [{ required: true, message: "公告标题为必填项", trigger: "blur" }],
  noticeType: [
    { required: true, message: "公告类型为必选项", trigger: "change" }
  ]
});
