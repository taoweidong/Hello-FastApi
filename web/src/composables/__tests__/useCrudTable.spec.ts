/**
 * useCrudTable 单元测试。
 *
 * 重点回归：
 * - 分页参数必须随 list 请求传递（分页功能的根基）；
 * - 搜索失败保留原数据并提示（不静默清空）；
 * - 删除区分"用户取消"与"请求失败"。
 */
import { beforeEach, describe, expect, it, vi } from "vitest";

const mockMessage = vi.fn();
vi.mock("@/utils/message", () => ({
  message: (...args: unknown[]) => mockMessage(...args)
}));

vi.mock("element-plus", () => ({
  ElMessageBox: { confirm: vi.fn() }
}));

import { ElMessageBox } from "element-plus";
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

  it("onSearch 传递分页参数 pageNum/pageSize", async () => {
    api.list.mockResolvedValue(pageResult([{ id: "1", name: "a" }], 1, 2, 20));
    const { pagination, onSearch } = setup();
    pagination.currentPage = 2;
    pagination.pageSize = 20;

    await onSearch();

    expect(api.list).toHaveBeenCalledWith(
      expect.objectContaining({ pageNum: 2, pageSize: 20 })
    );
    expect(pagination.total).toBe(1);
  });

  it("onSearch 剔除空字符串搜索条件（pruneEmpty）", async () => {
    api.list.mockResolvedValue(pageResult([]));
    const { onSearch } = setup({ name: "kw", isActive: "" });
    await onSearch();
    expect(api.list).toHaveBeenCalledWith(
      expect.not.objectContaining({ isActive: "" })
    );
    expect(api.list).toHaveBeenCalledWith(
      expect.objectContaining({ name: "kw" })
    );
  });

  it("请求失败时保留原数据并提示，不静默清空表格", async () => {
    api.list.mockResolvedValueOnce(pageResult([{ id: "1", name: "old" }]));
    const { dataList, onSearch } = setup();
    await onSearch();
    expect(dataList.value).toHaveLength(1);

    api.list.mockRejectedValueOnce(new Error("network"));
    await onSearch();
    expect(dataList.value).toHaveLength(1); // 保留旧数据
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("确认后删除成功会刷新列表", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.destroy.mockResolvedValue({ code: 0 });
    api.list.mockResolvedValue(pageResult([]));
    const { handleDelete, onSearch } = setup();
    const searchSpy = onSearch;

    await handleDelete({ id: "9", name: "目标" });

    expect(api.destroy).toHaveBeenCalledWith("9");
    expect(api.list).toHaveBeenCalled();
    void searchSpy;
  });

  it("用户取消删除时不调用删除接口", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockRejectedValue(
      "cancel"
    );
    const { handleDelete } = setup();

    await handleDelete({ id: "9", name: "目标" });

    expect(api.destroy).not.toHaveBeenCalled();
  });

  it("删除请求失败时提示错误", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.destroy.mockRejectedValue(new Error("500"));
    const { handleDelete } = setup();

    await handleDelete({ id: "9", name: "目标" });

    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("删除角色失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("handleSizeChange/handleCurrentChange 更新分页并重新搜索", async () => {
    api.list.mockResolvedValue(pageResult([], 0, 3, 50));
    const { pagination, handleSizeChange, handleCurrentChange } = setup();

    handleSizeChange(50);
    await nextTick();
    expect(api.list).toHaveBeenCalledWith(
      expect.objectContaining({ pageSize: 50 })
    );
    expect(pagination.pageSize).toBe(50); // 以服务端响应回写为准

    handleCurrentChange(3);
    await nextTick();
    expect(api.list).toHaveBeenCalledWith(
      expect.objectContaining({ pageNum: 3 })
    );
    expect(pagination.currentPage).toBe(3);
  });
});
