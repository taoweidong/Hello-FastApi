/**
 * 一次性脚本：收敛列表页的两处样式分叉。
 *
 * A. 搜索表单（.search-form）
 *    - 模板上 12 个页面各写了不同的 Tailwind 内边距类（pl-8 / pl-4 / pl-2、pt-3 / pt-2）；
 *    - scoped <style> 里又各自重复了一份 `.search-form { .el-form-item { margin-bottom } }`，
 *      其中 menu 页是 8px，其余 11 页是 12px。
 *
 * B. 主内容区（.main-content）
 *    - 7 个列表页各自重复 `margin: 8px 8px 0 !important`。
 *    - error / about 页的 `margin: 0 !important` 与 frame 的 `2px 0 0` 是**有意**的全屏/内嵌布局，
 *      脚本保留不动，靠 scoped 的更高特性值继续生效。
 *
 * 两处统一后由 style/element-plus.scss 中的全局规则 + 设计令牌（tokens.scss）驱动，
 * 窄屏时通过 --pure-search-form-padding / --pure-content-margin 自动收紧。
 *
 * 运行：node scripts/unify-search-form.mjs
 */
import { readFileSync, writeFileSync } from "node:fs";

const files = [
  "src/views/system/user/index.vue",
  "src/views/system/role/index.vue",
  "src/views/system/post/index.vue",
  "src/views/system/notice/index.vue",
  "src/views/system/menu/index.vue",
  "src/views/system/ip-rule/index.vue",
  "src/views/system/dept/index.vue",
  "src/views/system/config/index.vue",
  "src/views/monitor/online/index.vue",
  "src/views/monitor/logs/system/index.vue",
  "src/views/monitor/logs/operation/index.vue",
  "src/views/monitor/logs/login/index.vue",
  "src/views/welcome/index.vue"
];

/** 模板上的内边距类：pl-8 / pl-4 / pl-2 与 pt-3 / pt-2（顺序不定） */
const PADDING_CLASSES =
  /class="search-form bg-bg_color w-full (?:p[lrxtb]-\d+ )+(?=overflow-auto)/g;

/** scoped 里的 .search-form 块：`.search-form { :deep(.el-form-item){ margin-bottom: Npx } }` */
const SCOPED_SEARCH_FORM =
  /^[ \t]*\.search-form\s*\{[ \t]*\n(?:[ \t]*:deep\(\.el-form-item\)\s*\{[ \t]*\n[ \t]*margin-bottom:\s*\d+px;[ \t]*\n[ \t]*\}[ \t]*\n)?[ \t]*\}[ \t]*\n?/gm;

/** scoped 里的列表页 .main-content 块：`margin: 8px 8px 0 !important;` */
const SCOPED_MAIN_CONTENT =
  /^[ \t]*\.main-content\s*\{[ \t]*\n[ \t]*margin:\s*8px 8px 0 !important;[ \t]*\n[ \t]*\}[ \t]*\n?/gm;

/** 移除后残留的空 <style> 块 */
const EMPTY_STYLE = /\n?<style[^>]*>\s*(?:\n\s*)*<\/style>\n?/g;

/** 连续 3 个以上空行压成 1 个 */
const BLANK_LINES = /\n{3,}/g;

let changed = 0;
const report = [];

for (const file of files) {
  const original = readFileSync(file, "utf8");
  let next = original;

  const before = next;
  next = next.replace(PADDING_CLASSES, 'class="search-form bg-bg_color w-full ');
  if (next !== before) report.push(`${file}: 移除模板内边距类`);

  const beforeScoped = next;
  next = next.replace(SCOPED_SEARCH_FORM, "");
  if (next !== beforeScoped) report.push(`${file}: 移除重复 scoped .search-form 块`);

  const beforeMain = next;
  next = next.replace(SCOPED_MAIN_CONTENT, "");
  if (next !== beforeMain) report.push(`${file}: 移除重复 scoped .main-content 块`);

  next = next.replace(EMPTY_STYLE, "\n").replace(BLANK_LINES, "\n\n");

  if (next !== original) {
    writeFileSync(file, next);
    changed += 1;
  }
}

console.log(`已处理 ${changed} 个文件：`);
for (const line of report) console.log("  " + line);
