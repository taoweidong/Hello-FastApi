import { defineStore } from "pinia";
import {
  type multiType,
  type positionType,
  store,
  isUrl,
  isEqual,
  isNumber,
  isBoolean,
  getConfig,
  routerArrays,
  storageLocal,
  responsiveStorageNameSpace
} from "../utils";
import { usePermissionStoreHook } from "./permission";

/** 页签落盘防抖窗口（ms）：快速连续切换路由时合并写入 */
const TAGS_PERSIST_DELAY = 300;

/*
 * localStorage 落盘防抖 —— 自写 timer 实现，不依赖 @vueuse 的 useDebounceFn：
 * store 可能在 setup 作用域之外使用（useMultiTagsStoreHook 携带 store 实例），
 * 模块级 timer 与组件生命周期解耦，任何调用时机都安全。
 */
let tagsPersistTimer: ReturnType<typeof setTimeout> | null = null;

function persistTagsWithDebounce(multiTags: unknown): void {
  if (tagsPersistTimer !== null) clearTimeout(tagsPersistTimer);
  tagsPersistTimer = setTimeout(() => {
    tagsPersistTimer = null;
    storageLocal().setItem(`${responsiveStorageNameSpace()}tags`, multiTags);
  }, TAGS_PERSIST_DELAY);
}

function cancelPendingTagsPersist(): void {
  if (tagsPersistTimer !== null) {
    clearTimeout(tagsPersistTimer);
    tagsPersistTimer = null;
  }
}

export const useMultiTagsStore = defineStore("pure-multiTags", {
  state: () => ({
    // 存储标签页信息（路由信息）
    multiTags: storageLocal().getItem<StorageConfigs>(
      `${responsiveStorageNameSpace()}configure`
    )?.multiTagsCache
      ? storageLocal().getItem<StorageConfigs>(
          `${responsiveStorageNameSpace()}tags`
        )
      : ([
          ...routerArrays,
          ...usePermissionStoreHook().flatteningRoutes.filter(
            v => v?.meta?.fixedTag
          )
        ] as any),
    multiTagsCache: storageLocal().getItem<StorageConfigs>(
      `${responsiveStorageNameSpace()}configure`
    )?.multiTagsCache
  }),
  getters: {
    getMultiTagsCache(state) {
      return state.multiTagsCache;
    }
  },
  actions: {
    multiTagsCacheChange(multiTagsCache: boolean) {
      this.multiTagsCache = multiTagsCache;
      if (multiTagsCache) {
        // 300ms 防抖写入：传入 live 数组引用，落盘时即最新内容
        persistTagsWithDebounce(this.multiTags);
      } else {
        // 关闭缓存时取消待写入，防止 removeItem 之后又被防抖写回
        cancelPendingTagsPersist();
        storageLocal().removeItem(`${responsiveStorageNameSpace()}tags`);
      }
    },
    tagsCache(multiTags) {
      // 高频路径（每次路由切换 push/splice/equal 页签）合并为一次落盘
      this.getMultiTagsCache && persistTagsWithDebounce(multiTags);
    },
    handleTags<T>(
      mode: string,
      value?: T | multiType,
      position?: positionType
    ): T {
      switch (mode) {
        case "equal":
          this.multiTags = value;
          this.tagsCache(this.multiTags);
          break;
        case "push":
          {
            const tagVal = value as multiType;
            // 不添加到标签页
            if (tagVal?.meta?.hiddenTag) return;
            // 如果是外链无需添加信息到标签页
            if (isUrl(tagVal?.name)) return;
            // 如果title为空拒绝添加空信息到标签页
            if (tagVal?.meta?.title.length === 0) return;
            // showLink:false 不添加到标签页
            if (isBoolean(tagVal?.meta?.showLink) && !tagVal?.meta?.showLink)
              return;
            const tagPath = tagVal.path;
            const tagHasExits = this.multiTags.some(tag => {
              return (
                tag.path === tagPath &&
                isEqual(tag?.query, tagVal?.query) &&
                isEqual(tag?.params, tagVal?.params)
              );
            });

            if (tagHasExits) return;

            // 动态路由可打开的最大数量
            const dynamicLevel = tagVal?.meta?.dynamicLevel ?? -1;
            if (dynamicLevel > 0) {
              if (
                this.multiTags.filter(e => e?.path === tagPath).length >=
                dynamicLevel
              ) {
                // 如果当前已打开的动态路由数大于dynamicLevel，替换第一个动态路由标签
                const index = this.multiTags.findIndex(
                  item => item?.path === tagPath
                );
                index !== -1 && this.multiTags.splice(index, 1);
              }
            }
            this.multiTags.push(value);
            this.tagsCache(this.multiTags);
            if (
              getConfig()?.MaxTagsLevel &&
              isNumber(getConfig().MaxTagsLevel)
            ) {
              if (this.multiTags.length > getConfig().MaxTagsLevel) {
                this.multiTags.splice(1, 1);
              }
            }
          }
          break;
        case "splice":
          if (!position) {
            const index = this.multiTags.findIndex(v => v.path === value);
            if (index === -1) return;
            this.multiTags.splice(index, 1);
          } else {
            this.multiTags.splice(position?.startIndex, position?.length);
          }
          this.tagsCache(this.multiTags);
          return this.multiTags;
        case "slice":
          return this.multiTags.slice(-1);
      }
    }
  }
});

export function useMultiTagsStoreHook() {
  return useMultiTagsStore(store);
}
