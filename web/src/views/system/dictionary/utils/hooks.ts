import { computed } from "vue";
import { useDark } from "@pureadmin/utils";

export function usePublicHooks() {
  const { isDark } = useDark();

  const switchStyle = computed(() => {
    return {
      "--el-switch-on-color": "#6abe39",
      "--el-switch-off-color": "#e84749"
    };
  });

  const tagStyle = computed(() => {
    return (isActive: number) => {
      return isActive
        ? {
            "--el-tag-text-color": isDark.value ? "#6abe39" : "#389e0d",
            "--el-tag-bg-color": isDark.value ? "#172412" : "#f6ffed",
            "--el-tag-border-color": isDark.value ? "#274a17" : "#b7eb8f"
          }
        : {
            "--el-tag-text-color": isDark.value ? "#e84749" : "#cf1322",
            "--el-tag-bg-color": isDark.value ? "#2b1316" : "#fff1f0",
            "--el-tag-border-color": isDark.value ? "#58191c" : "#ffa39e"
          };
    };
  });

  return { isDark, switchStyle, tagStyle };
}

/** 格式化字典级联选择器选项（禁用已停用的字典项） */
export function formatHigherDictOptions(
  treeList: Array<Record<string, any>>
): Array<Record<string, any>> {
  if (!treeList || !treeList.length) return [];
  const newTreeList = [];
  for (let i = 0; i < treeList.length; i++) {
    treeList[i].disabled = !treeList[i].isActive;
    if (treeList[i].children) {
      formatHigherDictOptions(treeList[i].children);
    }
    newTreeList.push(treeList[i]);
  }
  return newTreeList;
}
