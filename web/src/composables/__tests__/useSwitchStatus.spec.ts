/**
 * useSwitchStatus 单元测试。
 *
 * 开关为受控模式（model-value）：点击不预翻转，确认且后端成功后才手动
 * 赋值翻转——因此无"先翻转、失败再回滚"的闪烁：
 * - 确认成功：updateStatus 收到目标状态（当前值取反），row.isActive 被赋为目标值；
 * - 请求失败 / 业务失败：开关保持原状态并本地提示；
 * - 用户取消：不调用接口，开关保持原状态。
 * 加载状态映射以 row.id 为键，分页/排序后不会错位。
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

  it("确认后调用 updateStatus 传目标状态，成功后受控翻转开关", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.updateStatus.mockResolvedValue({ code: 0 });
    const { onChange } = useSwitchStatus({
      api: api as never,
      displayField: "name",
      entityName: "角色"
    });
    // 行数据为当前值（停用中），点击切换为启用
    const row = { id: "1", name: "管理员", isActive: 0 };

    onChange({ row, index: 0 });
    await flushPromises();

    expect(api.updateStatus).toHaveBeenCalledWith("1", { isActive: 1 });
    expect(row.isActive).toBe(1); // 确认且成功后才翻转
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("已启用"),
      expect.objectContaining({ type: "success" })
    );
  });

  it("请求失败时开关保持原状态并提示（不预翻转，无需回滚）", async () => {
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

    expect(row.isActive).toBe(1); // 保持原状态
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("业务失败（code !== 0）时开关保持原状态并提示", async () => {
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.updateStatus.mockResolvedValue({ code: 500 });
    const { onChange } = useSwitchStatus({
      api: api as never,
      displayField: "name",
      entityName: "角色"
    });
    const row = { id: "1", name: "管理员", isActive: 1 };

    onChange({ row, index: 0 });
    await flushPromises();

    expect(row.isActive).toBe(1); // 保持原状态
    expect(mockMessage).toHaveBeenCalledWith(
      expect.stringContaining("失败"),
      expect.objectContaining({ type: "error" })
    );
  });

  it("用户取消确认时不调用接口且开关保持原状态", async () => {
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
    expect(row.isActive).toBe(1); // 受控模式下未翻转，无需回滚
  });

  it("加载状态映射以 row.id 为键", async () => {
    let resolveUpdate!: (value: unknown) => void;
    (ElMessageBox.confirm as ReturnType<typeof vi.fn>).mockResolvedValue(true);
    api.updateStatus.mockImplementation(
      () => new Promise(resolve => (resolveUpdate = resolve))
    );
    const { switchLoadMap, onChange } = useSwitchStatus({
      api: api as never,
      displayField: "name",
      entityName: "角色"
    });
    const row = { id: "42", name: "管理员", isActive: 1 };

    onChange({ row, index: 0 });
    await flushPromises();
    expect(switchLoadMap.value["42"]).toEqual({ loading: true });

    resolveUpdate({ code: 0 });
    await flushPromises();
    expect(switchLoadMap.value["42"]).toEqual({ loading: false });
  });
});
