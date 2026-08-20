<script setup lang="ts">
import { ref, reactive } from "vue";
import { message } from "@/utils/message";
import { changeMyPassword } from "@/api/user";
import { deviceDetection } from "@pureadmin/utils";
import type { FormInstance, FormRules } from "element-plus";

defineOptions({
  name: "AccountManagement"
});

const list = ref([
  {
    title: "账户密码",
    illustrate: "定期修改密码有助于保护账户安全",
    button: "修改"
  },
  {
    title: "密保手机",
    illustrate: "已绑定当前账户手机号",
    button: "修改"
  },
  {
    title: "备用邮箱",
    illustrate: "已绑定当前账户邮箱",
    button: "修改"
  }
]);

const dialogVisible = ref(false);
const saving = ref(false);
const pwdFormRef = ref<FormInstance>();
const pwdForm = reactive({
  oldPassword: "",
  newPassword: "",
  confirmPassword: ""
});

/** 确认密码一致性校验 */
const validateConfirm = (rule: any, value: string, callback: any) => {
  if (value !== pwdForm.newPassword) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const pwdRules = reactive<FormRules>({
  oldPassword: [
    { required: true, message: "当前密码为必填项", trigger: "blur" }
  ],
  newPassword: [
    { required: true, message: "新密码为必填项", trigger: "blur" },
    { min: 8, message: "密码长度至少 8 位", trigger: "blur" }
  ],
  confirmPassword: [
    { required: true, message: "确认密码为必填项", trigger: "blur" },
    { validator: validateConfirm, trigger: "blur" }
  ]
});

function onClick(item) {
  if (item.title === "账户密码") {
    pwdForm.oldPassword = "";
    pwdForm.newPassword = "";
    pwdForm.confirmPassword = "";
    dialogVisible.value = true;
    return;
  }
  message("请根据具体业务自行实现", { type: "info" });
}

async function onSubmitPwd(formEl: FormInstance) {
  await formEl.validate(async valid => {
    if (!valid) return;
    saving.value = true;
    try {
      const { code } = await changeMyPassword({
        oldPassword: pwdForm.oldPassword,
        newPassword: pwdForm.newPassword
      });
      if (code === 0) {
        message("密码修改成功", { type: "success" });
        dialogVisible.value = false;
      }
    } catch {
      message("密码修改失败，请检查当前密码是否正确", { type: "error" });
    } finally {
      saving.value = false;
    }
  });
}
</script>

<template>
  <div :class="['min-w-45', deviceDetection() ? 'max-w-full' : 'max-w-[70%]']">
    <h3 class="my-8!">账户管理</h3>
    <div v-for="(item, index) in list" :key="index">
      <div class="flex items-center">
        <div class="flex-1">
          <p>{{ item.title }}</p>
          <el-text class="mx-1" type="info">{{ item.illustrate }}</el-text>
        </div>
        <el-button type="primary" text @click="onClick(item)">
          {{ item.button }}
        </el-button>
      </div>
      <el-divider />
    </div>

    <el-dialog
      v-model="dialogVisible"
      title="修改账户密码"
      width="400px"
      destroy-on-close
      :closeOnClickModal="false"
    >
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="90px"
      >
        <el-form-item label="当前密码" prop="oldPassword">
          <el-input
            v-model="pwdForm.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="pwdForm.newPassword"
            type="password"
            show-password
            placeholder="至少 8 位，含大小写字母与数字"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="pwdForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="saving"
          @click="onSubmitPwd(pwdFormRef)"
        >
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style lang="scss" scoped>
.el-divider--horizontal {
  border-top: 0.1px var(--el-border-color) var(--el-border-style);
}
</style>
