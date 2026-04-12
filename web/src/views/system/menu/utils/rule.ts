import { reactive } from "vue";
import type { FormRules } from "element-plus";

/** 目录类型表单校验规则 */
export const dirFormRules = reactive(<FormRules>{
  name: [{ required: true, message: "路由名称为必填项", trigger: "blur" }],
  path: [{ required: true, message: "路由路径为必填项", trigger: "blur" }]
});

/** 页面类型表单校验规则 */
export const menuFormRules = reactive(<FormRules>{
  name: [{ required: true, message: "路由名称为必填项", trigger: "blur" }],
  path: [{ required: true, message: "路由路径为必填项", trigger: "blur" }],
  component: [
    { required: true, message: "组件路径为必填项", trigger: "blur" }
  ]
});

/** 权限类型表单校验规则 */
export const permissionFormRules = reactive(<FormRules>{
  name: [{ required: true, message: "权限名称为必填项", trigger: "blur" }],
  method: [{ required: true, message: "请求方法为必填项", trigger: "change" }]
});

/** 向后兼容：默认表单校验规则（同页面类型） */
export const formRules = menuFormRules;
