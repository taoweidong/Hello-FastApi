/**
 * 字典取数组合式函数（对标 RuoYi 的 useDict）
 *
 * 通过公开取数接口 GET /api/system/dictionary/type/{name} 拉取字典项，
 * 内置模块级缓存与并发请求去重，避免多组件重复请求同一字典类型。
 *
 * 用法：
 * ```ts
 * const dicts = useDict("sys_user_sex", "sys_active_status");
 * // dicts["sys_user_sex"] 为响应式的字典项数组 [{ label, value }]
 * ```
 */
import { onMounted, reactive } from "vue";
import { dictionaryApi } from "@/api/system/dictionary";

/** 字典项结构 */
export interface DictOption {
  label: string;
  value: string;
}

/** 模块级缓存：跨组件复用同一字典类型的取数结果 */
const dictCache = new Map<string, DictOption[]>();

/** 进行中的请求表：同一字典类型的并发请求去重 */
const pendingRequests = new Map<string, Promise<DictOption[]>>();

/** 根据字典类型名称获取字典项（带模块级缓存与并发去重） */
export function getDictItems(dictName: string): Promise<DictOption[]> {
  const cached = dictCache.get(dictName);
  if (cached) return Promise.resolve(cached);

  const pending = pendingRequests.get(dictName);
  if (pending) return pending;

  const task = dictionaryApi
    .getByType<DictOption[]>(dictName)
    .then(({ code, data }) => {
      const items = code === 0 && Array.isArray(data) ? data : [];
      dictCache.set(dictName, items);
      return items;
    })
    .catch(() => [] as DictOption[])
    .finally(() => pendingRequests.delete(dictName));
  pendingRequests.set(dictName, task);
  return task;
}

/** 清除字典缓存（字典数据变更后调用，dictName 缺省时清空全部） */
export function clearDictCache(dictName?: string): void {
  if (dictName) {
    dictCache.delete(dictName);
  } else {
    dictCache.clear();
  }
}

/**
 * 批量获取字典数据，返回以字典类型名称为键的响应式对象。
 *
 * @param dictNames 字典类型名称列表
 */
export function useDict(...dictNames: string[]) {
  const res = reactive<Record<string, DictOption[]>>(
    Object.fromEntries(dictNames.map(name => [name, [] as DictOption[]]))
  );
  onMounted(() => {
    dictNames.forEach(name => {
      getDictItems(name).then(items => {
        res[name] = items;
      });
    });
  });
  return res;
}

/** 从字典项列表中按值查找标签，未命中时返回回退值 */
export function dictLabel(
  options: DictOption[],
  value: string | number | null | undefined,
  fallback?: string
): string {
  if (value === null || value === undefined || value === "") {
    return fallback ?? "";
  }
  const matched = options.find(item => String(item.value) === String(value));
  return matched ? matched.label : (fallback ?? String(value));
}
