import { expect, test, type Page } from "@playwright/test";
import {
  apiFetch,
  apiLogin,
  gotoPage,
  makeUniqueName
} from "./utils/helpers";

/**
 * 角色管理：权限分配（菜单树）与数据权限 两个交互功能验证。
 *
 * 这两个功能是 /system/role 页面「操作」列里的「权限」「数据权限」入口，
 * 既有的 crud-role.spec.ts 只覆盖了 新增/修改/删除，未点击这两处。
 *
 * 为避免污染真实角色、并保证可清理，本用例在 beforeAll 用 API 创建一个
 * 专属测试角色（dataScope=全部、无菜单），两个用例复用它，afterAll 用 API 删除。
 */
test.describe.serial("角色管理-权限分配/数据权限交互", () => {
  const uniquePrefix = makeUniqueName("roleperm");
  const name = `${uniquePrefix}角色`;
  const code = `${uniquePrefix}code`;
  let roleId = "";

  async function searchRole(page: Page): Promise<void> {
    await page
      .locator('.search-form input[placeholder*="请输入角色标识"]')
      .fill(code);
    await page.getByRole("button", { name: "搜索" }).click();
  }

  function roleRow(page: Page) {
    return page.locator(".el-table__row", { hasText: code });
  }

  test.beforeAll(async () => {
    const token = await apiLogin("admin", "admin123");
    const res = await apiFetch("POST", "/api/system/role/create", {
      token,
      body: {
        name,
        code,
        isActive: 1,
        dataScope: 1,
        description: "e2e 权限分配/数据权限测试角色",
        menuIds: [],
        deptIds: []
      }
    });
    roleId = res.body?.data?.id ?? "";
    if (!roleId) {
      throw new Error(`创建测试角色失败: ${JSON.stringify(res)}`);
    }
  });

  test.afterAll(async () => {
    if (roleId) {
      const token = await apiLogin("admin", "admin123");
      await apiFetch("DELETE", `/api/system/role/${roleId}`, { token });
    }
  });

  test("菜单权限：打开权限面板、全选、保存", async ({ page }) => {
    await gotoPage(page, "/system/role");
    await searchRole(page);
    const row = roleRow(page);
    await expect(row.first()).toBeVisible({ timeout: 10000 });

    // 打开「权限」面板（操作列 -> 权限；exact 避免误匹配「数据权限」）
    await row.getByRole("button", { name: "权限", exact: true }).click();
    // 面板打开标志：唯一的「全选/全不选」复选框 + 菜单搜索框（二者均在面板内，
    // 出现即可证明面板（含菜单树）已渲染）
    await expect(page.getByText("全选/全不选").first()).toBeVisible({
      timeout: 10000
    });
    await expect(
      page.getByPlaceholder("请输入菜单进行搜索").first()
    ).toBeVisible();

    // 注：面板内的 el-tree-v2 为虚拟列表，根容器自身 0 尺寸、子节点绝对定位，
    // 且其挂载依赖 resize 驱动的 treeHeight 计算，attach/visible 判定不稳；
    // 故以「保存成功提示」作为「全选 -> 保存」整条链路生效的判据。
    // 全选/全不选 -> 保存
    await page.getByText("全选/全不选").click();
    // 保存（Check 图标按钮：面板容器内最后一个 size-5.5 图标，即「保存菜单权限」）
    const panel = page
      .getByPlaceholder("请输入菜单进行搜索")
      .first()
      .locator("xpath=ancestor::div[contains(@class,'bg-bg_color')]");
    const saveBtn = panel.locator(".size-5\\.5").last();
    await saveBtn.click();
    await expect(page.getByText(/菜单权限修改成功/).first()).toBeVisible({
      timeout: 10000
    });
  });

  test("数据权限：打开对话框、切换范围、保存", async ({ page }) => {
    await gotoPage(page, "/system/role");
    await searchRole(page);
    const row = roleRow(page);
    await expect(row.first()).toBeVisible({ timeout: 10000 });

    // 打开「数据权限」对话框（操作列 -> 数据权限）
    await row.getByRole("button", { name: "数据权限" }).click();
    const dialog = page.locator(".el-dialog", { hasText: "数据权限" });
    await expect(dialog).toBeVisible({ timeout: 10000 });

    // 切换为「仅本人数据权限」（不依赖自定义部门树，避免额外选部门）
    await dialog.getByText("仅本人数据权限").click();
    // 保存
    await dialog.getByRole("button", { name: "确定" }).click();
    await expect(page.getByText(/数据权限修改成功/).first()).toBeVisible({
      timeout: 10000
    });
  });
});
