/**
 * useSwitchStatus 单元测试。
 *
 * 重点回归：API 失败时开关回滚（UI 与后端状态一致）；用户取消不调用接口。
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
import { flushPromises } from "@vue/test-utils";
import { useSwitchStatus } from "../useSwitchStatus";

function makeApi() {
  return {
    updateStatus: vi.fn()
  } as unknown as {
    updateStatus: ReturnType<typeof vi.fn>;
  } as never;
}

describe("useSwitchStatus", () => {
  let api: { updateStatus: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    vi.clearAllMocks();
    api = makeApi() as unknown as { updateStatus: ReturnType<typeof vi.fn> };
  });

  it("确认后调用 updateStatus 并提示成功", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.updateStatus.mockResolvedValue({ code: 0 });
    const { onChange } = useSwitchStatus({
      api: api as never,
      displayField: "name",
      entityName: "角色"
    });
    const row = { id: "1", name: "管理员", isActive: 1 };

    onChange({ row, index: 0 });
    await flushPromises();

    expect(api.updateStatus).toHaveBeenCalledWith("1", { isActive: 1 });
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("已启用"),
      expect.objectContaining({ type: "success" })
    );
  });

  it("请求失败时回滚开关并提示", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.updateStatus.mockRejectedValue(new Error("500"));
    const { onChange } = useSwitchStatus({
      api: api as never,
      displayField: "name",
      entityName: "角色"
    });
    const row = { id: "1", name: "管理员", isActive: 1 };

    onChange({ row, index: 0 });
    await flushPromises();

    expect(row.isActive).toBe(0); // 回滚
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("用户取消时回滚开关且不调用接口", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockRejectedValue(
      "cancel"
    );
    const { onChange } = useSwitchStatus({
      api: api as never,
      displayField: "name",
      entityName: "角色"
    });
    const row = { id: "1", name: "管理员", isActive: 1 };

    onChange({ row, index: 0 });
    await flushPromises();

    expect(api.updateStatus).not.toHaveBeenCalled();
    expect(row.isActive).toBe(0); // el-switch 已本地切换，取消后回滚
  });
});
