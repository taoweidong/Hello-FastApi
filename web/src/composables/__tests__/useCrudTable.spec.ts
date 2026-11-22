/**
 * useCrudTable 单元测试。
 *
 * 重点回归：
 * - 分页参数必须随 list 请求传递（分页功能的根基），请求竞态防护注入的
 *   第二参 config.signal（AbortSignal）一并断言；
 * - 查询失败保留原数据：网络类错误（无响应/5xx）静默（全局拦截器已提示），
 *   业务错误（4xx）本地提示，避免同一失败弹两层 toast；
 * - 连续 onSearch 时上一次请求被 abort，取消错误完全静默，且不覆盖最新
 *   数据、不复位 loading（由最新请求接管）；
 * - 删除确认已由页面 popconfirm 负责，hook 直接执行删除（不再弹 MessageBox）；
 * - 删除后当前页删空时页码回退，避免落在空页；改 pageSize 回到第 1 页。
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockMessage = vi.fn();
vi.mock("@/utils/message", () => ({
  message: (...args: unknown[]) => mockMessage(...args)
}));

import { nextTick } from "vue";
import { useCrudTable } from "../useCrudTable";
import type { BaseApi } from "@/api/base";

type Row = { id: string; name: string };

function makeApi() {
  return {
    list: vi.fn(),
    destroy: vi.fn(),
    batchDelete: vi.fn()
  } as unknown as BaseApi<Row, Row, Record<string, unknown>> & {
    list: ReturnType<typeof vi.fn>;
    destroy: ReturnType<typeof vi.fn>;
    batchDelete: ReturnType<typeof vi.fn>;
  };
}

function pageResult(
  list: Row[],
  total = list.length,
  pageNum = 1,
  pageSize = 10
) {
  return {
    code: 0,
    message: "ok",
    data: { list, total, pageSize, currentPage: pageNum }
  };
}

/** list 调用签名为 (params, config)：竞态防护始终注入 AbortSignal */
const withSignal = expect.objectContaining({
  signal: expect.any(AbortSignal)
});

/** 构造一个与 axios ERR_CANCELED 同形的取消错误 */
function canceledError() {
  return Object.assign(new Error("canceled"), { code: "ERR_CANCELED" });
}

describe("useCrudTable", () => {
  let api: ReturnType<typeof makeApi>;

  beforeEach(() => {
    vi.clearAllMocks();
    api = makeApi();
  });

  function setup(searchForm: Record<string, unknown> = {}) {
    return useCrudTable<Row>({
      api,
      searchForm,
      displayField: "name",
      entityName: "角色",
      immediate: false
    });
  }

  it("onSearch 传递分页参数 pageNum/pageSize 并注入 AbortSignal", async () => {
    api.list.mockResolvedValue(pageResult([{ id: "1", name: "a" }], 1, 2, 20));
    const { pagination, onSearch } = setup();
    pagination.currentPage = 2;
    pagination.pageSize = 20;

    await onSearch();

    expect(api.list).toHaveBeenCalledWith(
      expect.objectContaining({ pageNum: 2, pageSize: 20 }),
      withSignal
    );
    expect(pagination.total).toBe(1);
  });

  it("onSearch 剔除空字符串搜索条件（pruneEmpty）", async () => {
    api.list.mockResolvedValue(pageResult([]));
    const { onSearch } = setup({ name: "kw", isActive: "" });
    await onSearch();
    expect(api.list).toHaveBeenCalledWith(
      expect.not.objectContaining({ isActive: "" }),
      withSignal
    );
    expect(api.list).toHaveBeenCalledWith(
      expect.objectContaining({ name: "kw" }),
      withSignal
    );
  });

  it("网络类错误（无响应/5xx）静默：保留原数据且不重复弹提示", async () => {
    api.list.mockResolvedValueOnce(pageResult([{ id: "1", name: "old" }]));
    const { dataList, onSearch } = setup();
    await onSearch();
    expect(dataList.value).toHaveLength(1);

    // 无响应（断网/超时）：全局拦截器已提示，页面层静默
    api.list.mockRejectedValueOnce(new Error("network"));
    await onSearch();
    expect(dataList.value).toHaveLength(1); // 保留旧数据
    expect(mockMessage).not.toHaveBeenCalled();

    // 5xx：同上
    api.list.mockRejectedValueOnce({ response: { status: 502 } });
    await onSearch();
    expect(dataList.value).toHaveLength(1);
    expect(mockMessage).not.toHaveBeenCalled();
  });

  it("业务错误（4xx）时保留原数据并本地提示，不静默清空表格", async () => {
    api.list.mockResolvedValueOnce(pageResult([{ id: "1", name: "old" }]));
    const { dataList, onSearch } = setup();
    await onSearch();
    expect(dataList.value).toHaveLength(1);

    api.list.mockRejectedValueOnce({ response: { status: 400 } });
    await onSearch();
    expect(dataList.value).toHaveLength(1); // 保留旧数据
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("连续两次 onSearch：上一次未完成请求被 abort，取消错误静默", async () => {
    const signals: AbortSignal[] = [];
    api.list.mockImplementation(
      (_params: unknown, config: { signal: AbortSignal }) => {
        signals.push(config.signal);
        return new Promise((resolve, reject) => {
          // 被 abort 时以取消错误结束，模拟 axios 取消行为
          config.signal.addEventListener("abort", () =>
            reject(canceledError())
          );
          if (signals.length > 1) {
            resolve(pageResult([{ id: "2", name: "new" }]));
          }
        });
      }
    );

    const { dataList, onSearch } = setup();
    const first = onSearch(); // 第一次搜索挂起
    await onSearch(); // 第二次搜索发起时取消第一次

    expect(signals[0].aborted).toBe(true);
    expect(signals[1].aborted).toBe(false);
    expect(dataList.value).toEqual([{ id: "2", name: "new" }]);

    await first; // 第一次以取消错误收尾：不弹提示、不覆盖数据
    expect(mockMessage).not.toHaveBeenCalled();
    expect(dataList.value).toEqual([{ id: "2", name: "new" }]);
  });

  it("被取消的请求不复位 loading（由最新请求接管），迟到响应不覆盖最新数据", async () => {
    let resolveFirst!: (value: unknown) => void;
    api.list.mockImplementationOnce(
      () => new Promise(resolve => (resolveFirst = resolve))
    );
    api.list.mockResolvedValueOnce(pageResult([{ id: "2", name: "new" }]));

    const { dataList, loading, onSearch } = setup();
    const first = onSearch(); // 第一次搜索挂起
    expect(loading.value).toBe(true);

    const second = onSearch(); // 取消第一次，第二次进行中接管 loading
    expect(loading.value).toBe(true);
    await second;
    expect(dataList.value).toEqual([{ id: "2", name: "new" }]);

    // 第一次的慢响应迟到（abort 后才 resolve）：静默丢弃，不覆盖新结果
    resolveFirst(pageResult([{ id: "1", name: "stale" }], 1, 1, 10));
    await first;
    expect(dataList.value).toEqual([{ id: "2", name: "new" }]);
    expect(loading.value).toBe(false);
  });

  it("删除成功会刷新列表（确认由页面 popconfirm 负责）", async () => {
    api.destroy.mockResolvedValue({ code: 0 });
    api.list.mockResolvedValue(pageResult([]));
    const { handleDelete } = setup();

    await handleDelete({ id: "9", name: "目标" });

    expect(api.destroy).toHaveBeenCalledWith("9");
    expect(api.list).toHaveBeenCalled();
  });

  it("删除请求失败时提示错误", async () => {
    api.destroy.mockRejectedValue(new Error("500"));
    const { handleDelete } = setup();

    await handleDelete({ id: "9", name: "目标" });

    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("删除角色失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("删除当前页最后一条且不在首页时，页码回退避免空页", async () => {
    api.list.mockImplementation(async (params: any) =>
      pageResult(
        params.pageNum === 2 ? [{ id: "9", name: "目标" }] : [],
        11,
        params.pageNum,
        10
      )
    );
    const { handleDelete, pagination, dataList, onSearch } = setup();
    pagination.currentPage = 2;
    await onSearch();
    expect(dataList.value).toHaveLength(1); // 第 2 页仅剩一条

    api.destroy.mockResolvedValue({ code: 0 });
    await handleDelete({ id: "9", name: "目标" });

    expect(api.destroy).toHaveBeenCalledWith("9");
    expect(pagination.currentPage).toBe(1);
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ pageNum: 1, pageSize: 10 }),
      withSignal
    );
  });

  it("删除非当前页最后一条时保持页码不变", async () => {
    api.list.mockImplementation(async (params: any) =>
      pageResult(
        params.pageNum === 2
          ? [
              { id: "1", name: "a" },
              { id: "9", name: "b" }
            ]
          : [],
        12,
        params.pageNum,
        10
      )
    );
    const { handleDelete, pagination, onSearch } = setup();
    pagination.currentPage = 2;
    await onSearch();

    api.destroy.mockResolvedValue({ code: 0 });
    await handleDelete({ id: "9", name: "b" });

    expect(pagination.currentPage).toBe(2);
  });

  it("批量删除清空当前页且不在首页时，页码回退避免空页", async () => {
    api.list.mockImplementation(async (params: any) =>
      pageResult(
        params.pageNum === 2 ? [{ id: "1", name: "a" }] : [],
        11,
        params.pageNum,
        10
      )
    );
    const { handleBatchDelete, pagination, dataList, onSearch } = setup();
    pagination.currentPage = 2;
    await onSearch();
    expect(dataList.value).toHaveLength(1);

    api.batchDelete.mockResolvedValue({ code: 0 });
    await handleBatchDelete(["1"]);

    expect(api.batchDelete).toHaveBeenCalledWith(["1"]);
    expect(pagination.currentPage).toBe(1);
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ pageNum: 1 }),
      withSignal
    );
  });

  it("handleSizeChange/handleCurrentChange 更新分页并重新搜索", async () => {
    api.list.mockResolvedValue(pageResult([], 0, 3, 50));
    const { pagination, handleSizeChange, handleCurrentChange } = setup();

    handleSizeChange(50);
    await nextTick();
    // 改 pageSize 后旧页码可能超出新的总页数，必须回到第 1 页再查询
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ pageNum: 1, pageSize: 50 }),
      withSignal
    );
    expect(pagination.pageSize).toBe(50); // 以服务端响应回写为准

    handleCurrentChange(3);
    await nextTick();
    expect(api.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ pageNum: 3 }),
      withSignal
    );
    expect(pagination.currentPage).toBe(3);
  });
});
