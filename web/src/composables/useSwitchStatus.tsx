/**
 * useSwitchStatus - 通用状态开关切换逻辑
 *
 * 封装 el-switch 状态切换的确认弹窗、API 调用、加载状态管理。
 * 配合 useCrudTable 使用，消除每个 hook.tsx 中重复的 onChange 代码。
 *
 * 开关采用受控模式（model-value）：点击不立即翻转，确认且后端成功后才
 * 手动赋值翻转，消除"先视觉翻转、失败/取消再回滚"的闪烁；
 * 加载状态映射以 row.id 为键，避免分页/排序后按 index 键控错位。
 */
import { message } from "@/utils/message";
import type { BaseApi } from "@/api/base";
import { ElMessageBox } from "element-plus";
import { computed, ref, type Ref, type ComputedRef } from "vue";

/** useSwitchStatus 配置项 */
export interface UseSwitchStatusOptions {
  /** BaseApi 实例，需支持 updateStatus 方法 */
  api: BaseApi;
  /** 删除确认时显示的字段名，如 "name"、"username" */
  displayField: string;
  /** 实体中文名，如 "角色"、"用户" */
  entityName: string;
}

/** useSwitchStatus 返回值 */
export interface UseSwitchStatusReturn {
  /** 每行开关的加载状态映射（以 row.id 为键，分页/排序后不会错位） */
  switchLoadMap: Ref<Record<string | number, { loading: boolean }>>;
  /** 开关样式（绿色启用/红色停用） */
  switchStyle: ComputedRef<Record<string, string>>;
  /** 状态变更处理函数 */
  onChange: (scope: { row: any; index?: number }) => void;
  /**
   * 创建开关列的 cellRenderer
   * @returns 可直接赋值给 column.cellRenderer 的函数
   */
  createSwitchRenderer: () => (scope: any) => any;
}

export function useSwitchStatus(
  options: UseSwitchStatusOptions
): UseSwitchStatusReturn {
  const { api, displayField, entityName } = options;

  const switchLoadMap = ref<Record<string | number, { loading: boolean }>>({});

  /** 开关样式：绿色启用、红色停用 */
  const switchStyle = computed(() => ({
    "--el-switch-on-color": "#6abe39",
    "--el-switch-off-color": "#e84749"
  }));

  /** 状态变更确认 + API 调用（受控模式：点击时行数据尚未翻转，目标状态取反） */
  function onChange({ row }: { row: any; index?: number }) {
    const target = row.isActive === 1 ? 0 : 1;
    ElMessageBox.confirm(
      `确认要<strong>${
        target === 1 ? "启用" : "停用"
      }</strong><strong style='color:var(--el-color-primary)'>${
        row[displayField]
      }</strong>吗?`,
      "系统提示",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
        dangerouslyUseHTMLString: true,
        draggable: true
      }
    )
      .then(async () => {
        switchLoadMap.value[row.id] = Object.assign(
          {},
          switchLoadMap.value[row.id],
          { loading: true }
        );
        try {
          const { code } = await api.updateStatus(row.id, {
            isActive: target
          });
          if (code === 0) {
            // 确认且后端成功后才受控翻转开关
            row.isActive = target;
            message(
              `已${target === 1 ? "启用" : "停用"}${entityName} ${row[displayField]}`,
              {
                type: "success"
              }
            );
          } else {
            message(`修改${entityName}状态失败`, { type: "error" });
          }
        } catch {
          message(`修改${entityName}状态失败`, { type: "error" });
        } finally {
          switchLoadMap.value[row.id] = Object.assign(
            {},
            switchLoadMap.value[row.id],
            { loading: false }
          );
        }
      })
      .catch(() => {
        // 用户取消确认：开关保持原状态（受控模式下无需回滚）
      });
  }

  /**
   * 创建开关列的 cellRenderer
   * 用法：columns 中 `{ label: "状态", cellRenderer: createSwitchRenderer() }`
   */
  function createSwitchRenderer() {
    return (scope: any) => (
      <el-switch
        size={scope.props.size === "small" ? "small" : "default"}
        loading={switchLoadMap.value[scope.row.id]?.loading}
        model-value={scope.row.isActive}
        active-value={1}
        inactive-value={0}
        active-text="已启用"
        inactive-text="已停用"
        inline-prompt
        style={switchStyle.value}
        onChange={() => onChange(scope)}
      />
    );
  }

  return {
    switchLoadMap,
    switchStyle,
    onChange,
    createSwitchRenderer
  };
}
