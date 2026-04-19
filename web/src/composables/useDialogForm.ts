/**
 * useDialogForm - 通用对话框表单逻辑
 *
 * 封装 addDialog + 表单验证 + 提交逻辑，消除每个 hook.tsx 中重复的
 * openDialog / beforeSure / validate / create/update 代码。
 */
import { message } from "@/utils/message";
import { BaseApi } from "@/api/base";
import { addDialog } from "@/components/ReDialog";
import { deviceDetection } from "@pureadmin/utils";
import type { Component } from "vue";
import { ref, h, type Ref } from "vue";

/** 字段映射配置 */
export interface FieldMapping {
  /** 字段名，同时用于表单和 API payload */
  key: string;
  /** 新增时的默认值 */
  defaultValue?: any;
  /** 是否可为空（空字符串自动转为 null） */
  nullable?: boolean;
  /** 从 row 中取值的字段名（默认与 key 相同） */
  rowKey?: string;
}

/** useDialogForm 配置项 */
export interface UseDialogFormOptions {
  /** 表单 Vue 组件 */
  formComponent: Component;
  /** 实体中文名，如 "角色"、"用户" */
  entityName: string;
  /** 字段映射配置 */
  fieldMappings: FieldMapping[];
  /** BaseApi 实例 */
  api: BaseApi;
  /** 对话框宽度，默认 "40%" */
  width?: string;
  /** 新增/更新成功后的回调（通常为 onSearch） */
  onSuccess?: () => void;
}

/** useDialogForm 返回值 */
export interface UseDialogFormReturn {
  /** 表单组件 ref（内部使用） */
  formRef: Ref<any>;
  /** 打开对话框 */
  openDialog: (title?: string, row?: any) => void;
}

export function useDialogForm(options: UseDialogFormOptions): UseDialogFormReturn {
  const {
    formComponent,
    entityName,
    fieldMappings,
    api,
    width = "40%",
    onSuccess
  } = options;

  const formRef = ref();

  /**
   * 构建表单初始数据
   * @param row 编辑时的行数据（新增时为 undefined）
   */
  function buildFormInline(row?: any) {
    const result: Record<string, any> = {};
    for (const mapping of fieldMappings) {
      const sourceKey = mapping.rowKey || mapping.key;
      if (row) {
        result[mapping.key] = row[sourceKey] ?? mapping.defaultValue ?? "";
      } else {
        result[mapping.key] = mapping.defaultValue ?? "";
      }
    }
    return result;
  }

  /**
   * 从表单数据构建 API payload
   * @param formInline 表单数据
   */
  function buildPayload(formInline: Record<string, any>) {
    const payload: Record<string, any> = {};
    for (const mapping of fieldMappings) {
      const value = formInline[mapping.key];
      payload[mapping.key] = mapping.nullable && !value ? null : value;
    }
    return payload;
  }

  /** 打开对话框 */
  function openDialog(title = "新增", row?: any) {
    addDialog({
      title: `${title}${entityName}`,
      props: {
        formInline: buildFormInline(row)
      },
      width,
      draggable: true,
      fullscreen: deviceDetection(),
      fullscreenIcon: true,
      closeOnClickModal: false,
      contentRenderer: () =>
        h(formComponent, { ref: formRef, formInline: null }),
      beforeSure: (done, { options }) => {
        const FormRef = formRef.value.getRef();
        const curData = options.props.formInline as Record<string, any>;

        FormRef.validate(async (valid: boolean) => {
          if (valid) {
            try {
              const payload = buildPayload(curData);

              if (title === "新增") {
                const { code } = await api.create(payload);
                if (code === 0 || code === 201) {
                  // 找到第一个字符串类型的字段作为显示名
                  const displayName =
                    curData[fieldMappings.find(m => !m.nullable)?.key || "name"];
                  message(`成功创建${entityName} ${displayName ?? ""}`, {
                    type: "success"
                  });
                  done();
                  onSuccess?.();
                }
              } else {
                const { code } = await api.partialUpdate(row.id, payload);
                if (code === 0) {
                  const displayName =
                    curData[fieldMappings.find(m => !m.nullable)?.key || "name"];
                  message(`成功更新${entityName} ${displayName ?? ""}`, {
                    type: "success"
                  });
                  done();
                  onSuccess?.();
                }
              }
            } catch {
              message(`${title}${entityName}失败`, { type: "error" });
            }
          }
        });
      }
    });
  }

  return {
    formRef,
    openDialog
  };
}
