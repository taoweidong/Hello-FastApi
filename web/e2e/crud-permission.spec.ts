import { expect, test } from "@playwright/test";
import { gotoPage } from "./utils/helpers";

/**
 * 权限演示页交互验证（原 smoke 仅做只读锚点断言，此处补齐「交互/权限可见性」验证）。
 *
 * 注意：/permission/page/index 的「角色切换」下拉一旦真正选中会触发
 * loginByUsername 重新登录为 common 用户并写入共享 storageState，从而破坏
 * serial crud 项目其余用例依赖的 admin 会话。因此本用例只验证下拉与选项渲染，
 * 不触发 @change，避免污染 admin 共享会话。
 */
test.describe("权限演示页交互验证", () => {
  test("页面权限：角色切换下拉与两个选项渲染", async ({ page }) => {
    await gotoPage(page, "/permission/page/index");

    // 卡片标题与「当前角色」展示
    await expect(page.getByText("当前角色：").first()).toBeVisible({
      timeout: 10000
    });

    // 角色下拉与两个选项渲染（仅展开，不选中）
    const select = page.locator(".el-select").first();
    await expect(select).toBeVisible();
    await select.click();
    await expect(page.getByText("管理员角色").first()).toBeVisible();
    await expect(page.getByText("普通角色").first()).toBeVisible();
    // 收起下拉，不触发 @change（避免重新登录破坏 admin 会话）
    await page.keyboard.press("Escape");
  });

  test("按钮权限（路由 meta.auths）：三种判断方式的按钮均可见", async ({
    page
  }) => {
    await gotoPage(page, "/permission/button/index");

    // 当前 code 列表文本（来自 router.currentRoute.meta.auths）
    await expect(page.getByText("当前拥有的code列表：").first()).toBeVisible({
      timeout: 10000
    });
    // 三类卡片标题
    await expect(page.getByText("组件方式判断权限").first()).toBeVisible();
    await expect(page.getByText("函数方式判断权限").first()).toBeVisible();
    await expect(page.getByText("指令方式判断权限").first()).toBeVisible();

    // 三种权限按钮可见：admin 经 _build_route_tree 从 PermissionButton 目录
    // 继承了 permission:btn:*，故 hasAuth / Auth / v-auth 均判定通过
    await expect(
      page
        .getByRole("button", { name: /拥有code：'permission:btn:add'/ })
        .first()
    ).toBeVisible();
    await expect(
      page
        .getByRole("button", { name: /拥有code：\['permission:btn:edit'\]/ })
        .first()
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /permission:btn:delete/ }).first()
    ).toBeVisible();
  });

  test("按钮权限（登录 permissions 扁平码表）：按钮可见", async ({ page }) => {
    await gotoPage(page, "/permission/button/perms");

    // 当前菜单权限列表（admin 为超级用户，permissions 是「全部权限码」扁平列表，
    // 而非 ['*:*:*'] 通配符，因此下方的「*:*:* 代表拥有全部」提示对 admin 不展示——
    // 该提示仅在登录 permissions[0] === '*:*:*' 时可见）
    await expect(
      page.getByText("当前拥有的菜单权限列表：").first()
    ).toBeVisible({ timeout: 10000 });

    // 组件/函数/指令三种方式的按钮均因 admin 拥有对应权限码而可见
    await expect(
      page
        .getByRole("button", { name: /拥有code：'permission:btn:add'/ })
        .first()
    ).toBeVisible();
    await expect(
      page
        .getByRole("button", { name: /拥有code：\['permission:btn:edit'\]/ })
        .first()
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: /permission:btn:delete/ }).first()
    ).toBeVisible();
  });
});
