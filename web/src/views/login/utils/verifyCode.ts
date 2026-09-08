import type { FormInstance, FormItemProp } from "element-plus";
import { clone } from "@pureadmin/utils";
import { ref, onUnmounted } from "vue";

const isDisabled = ref(false);
const timer = ref(null);
const text = ref("");

export const useVerifyCode = () => {
  /** 清除倒计时定时器并复位状态 */
  const end = () => {
    text.value = "";
    isDisabled.value = false;
    clearInterval(timer.value);
    timer.value = null;
  };

  // 组件卸载时清理定时器，避免切换页面后 setInterval 继续运行造成内存泄漏
  onUnmounted(end);
  const start = async (
    formEl: FormInstance | undefined,
    props: FormItemProp,
    time = 60
  ) => {
    if (!formEl) return;
    const initTime = clone(time, true);
    await formEl.validateField(props, isValid => {
      if (isValid) {
        clearInterval(timer.value);
        isDisabled.value = true;
        text.value = `${time}`;
        timer.value = setInterval(() => {
          if (time > 0) {
            time -= 1;
            text.value = `${time}`;
          } else {
            text.value = "";
            isDisabled.value = false;
            clearInterval(timer.value);
            time = initTime;
          }
        }, 1000);
      }
    });
  };

  return {
    isDisabled,
    timer,
    text,
    start,
    end
  };
};
