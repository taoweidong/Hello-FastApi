/**
 * useSwitchStatus - 通用状态开关切换逻辑
 *
 * 封装 el-switch 状态切换的确认弹窗、API 调用、加载状态管理。
 * 配合 useCrudTable 使用，消除每个 hook.tsx 中重复的 onChange 代码。
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
  /** 每行开关的加载状态映射 */
  switchLoadMap: Ref<Record<number, { loading: boolean }>>;
  /** 开关样式（绿色启用/红色停用） */
  switchStyle: ComputedRef<Record<string, string>>;
  /** 状态变更处理函数 */
  onChange: (scope: { row: any; index: number }) => void;
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

  const switchLoadMap = ref<Record<number, { loading: boolean }>>({});

  /** 开关样式：绿色启用、红色停用 */
  const switchStyle = computed(() => ({
    "--el-switch-on-color": "#6abe39",
    "--el-switch-off-color": "#e84749"
  }));

  /** 状态变更确认 + API 调用 */
  function onChange({ row, index }: { row: any; index: number }) {
    ElMessageBox.confirm(
      `确认要<strong>${!row.isActive ? "停用" : "启用"}</strong><strong style='color:var(--el-color-primary)'>${row[displayField]}</strong>吗?`,
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
        switchLoadMap.value[index] = Object.assign(
          {},
          switchLoadMap.value[index],
          { loading: true }
        );
        try {
          const { code } = await api.updateStatus(row.id, {
            isActive: row.isActive
          });
          if (code === 0) {
            message(
              `已${row.isActive ? "启用" : "停用"}${entityName} ${row[displayField]}`,
              {
                type: "success"
              }
            );
          }
        } catch {
          row.isActive = row.isActive === 1 ? 0 : 1;
          message(`修改${entityName}状态失败`, { type: "error" });
        } finally {
          switchLoadMap.value[index] = Object.assign(
            {},
            switchLoadMap.value[index],
            { loading: false }
          );
        }
      })
      .catch(() => {
        row.isActive = row.isActive === 1 ? 0 : 1;
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
        loading={switchLoadMap.value[scope.index]?.loading}
        v-model={scope.row.isActive}
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
