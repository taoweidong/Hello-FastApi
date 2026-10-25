# pytest 误伤开发库（schema 漂移）问题修复

> 2026-10-25。现象：每次全量跑 pytest 后，`service/sql/dev.db` 的 `sys_userloginlog.username`
> 列会被删掉，而 `alembic_version` 仍停在 head——「版本戳超前、结构落后」。
> 直接后果：E2E 的 `/api/system/login-logs` 500（`no column named username`）。

## 1. 根因

三个缺陷叠加，缺一不可：

1. **`alembic/env.py` 用裸 `Settings()` 取 DATABASE_URL**（而非 `get_settings()`）。
   裸构造器的 `model_config` 只认 `.env`，而本项目**没有 `.env` 文件**
   （只有 `.env.development/.env.testing/.env.production/.env.local`）；
   且 testing 环境的库地址覆盖（`_ENV_OVERRIDES["testing"]["DATABASE_URL"]=.../test.db`）
   **只在 `get_settings()` 里应用**。于是 `APP_ENV=testing` 时 alembic 静默落到
   **模型默认值** `sqlite+aiosqlite:///./sql/dev.db`。
   实测证据：

   ```text
   APP_ENV=testing  bare Settings().DATABASE_URL = sqlite+aiosqlite:///./sql/dev.db  ← 开发库
   APP_ENV=testing  get_settings().DATABASE_URL  = sqlite+aiosqlite:///./sql/test.db  ← 正确
   ```

2. **`tests/unit/test_alembic_cli.py` 用子进程真实执行 alembic 命令**，
   且未隔离数据库。pytest 进程 `APP_ENV=testing`（conftest `setdefault`），
   子进程原样继承 → 三个命令全部打在 dev.db 上：
   - `test_migrate_command_runs` → `alembic upgrade head`（已在 head，空转）
   - `test_rollback_command_exists` → `alembic downgrade -1` → 执行
     `c4d5e6f7a8b9.downgrade()` → **DROP COLUMN username**
   - `test_stamp_command_exists` → `alembic stamp head` → 版本戳推回 head，
     **但不补 Schema**

   净效果：列丢了、版本戳还是 head。迁移自身的 upgrade 是幂等的（有列存在性检查），
   所以后续 `upgrade head` 也不会自愈——**每次跑 pytest 复发一次**。

3. `scripts/cli.py` 的 `initdb` 现已委托 `run_migrate()`（走 alembic），
   同样受缺陷 1 影响。

决定性实验（全量 pytest 前后检查 dev.db）：

```text
BEFORE: username 列存在 = True
2171 passed in 605.20s
AFTER:  username 列存在 = False   （alembic_version 仍为 c4d5e6f7a8b9 head）
```

## 2. 修复

| # | 文件 | 改动 |
|---|---|---|
| 1 | `service/alembic/env.py` | 裸 `Settings()` → `get_settings()`，让 alembic 与 App 共用同一套环境配置解析（`.env.{APP_ENV}` 链 + 环境覆盖）。附带修掉一个生产隐患：APP_ENV=production 时裸构造同样会落到 dev.db。顺带补上 `do_run_migrations(connection)` 缺失的参数标注（mypy 清零） |
| 2 | `service/tests/unit/test_alembic_cli.py` |  hermetic 化：`_cli_env()` 经 `tmp_path` + `DATABASE_URL` 环境变量把子进程库指向临时文件；rollback 测试改为 `migrate → rollback -1 → migrate` 闭环序列（旧版先 `initdb` 再 downgrade，在无版本表的库上回滚必然失败）。选 `APP_ENV=development` 而非 testing：testing 的库覆盖以构造参数传入、优先级高于环境变量，会盖掉临时地址。同时补齐泛型/返回类型标注（mypy 由 3 错→0 错） |
| 3 | `service/sql/dev.db` | 修复漂移：`alembic stamp a3b5c7d9e1f2` → `upgrade head`（upgrade 幂等）→ 全表结构核对 `SQLModel.metadata ↔ PRAGMA table_info`，16 表零漂移 |

## 3. 验证

| 项 | 结果 |
|---|---|
| `pytest tests/unit/test_alembic_cli.py` | 3/3 通过；dev.db BEFORE/AFTER 完全一致（username=True, version=head） |
| 全量 pytest | **2171 passed in 493.68s**；dev.db BEFORE/AFTER 完全一致（username=True, version=c4d5e6f7a8b9）——抹库行为彻底消失，且较修复前（605.20s）快了近 2 分钟 |
| dev.db 结构核对 | 16 张模型表齐全、无列级漂移、91 行登录日志数据保留 |
| E2E（Playwright，串行） | **51/51 通过（2.4m）**，`/api/system/login-logs` 不再 500 |
| mypy | `alembic/env.py`、`tests/unit/test_alembic_cli.py` 均由报错清零（env.py 原有 1 个、测试文件原有 3 个） |

## 4. 防护约定（沉淀）

- **裸 `Settings()` 是 footgun**：全仓库仅允许在 `src/config/settings.py` 内部使用；
  任何需要「按 APP_ENV 解析配置」的调用方（alembic env、脚本、工具）一律走 `get_settings()`。
  判别方法：`APP_ENV=testing python -c "from src.config.settings import Settings, get_settings; print(Settings().DATABASE_URL, get_settings().DATABASE_URL)"`，两者必须一致。
- **子进程测试必须隔离数据库**：凡测试通过 `subprocess` 触发 alembic/cli，一律用
  `tmp_path` + `DATABASE_URL` 环境变量指向临时文件；`APP_ENV=development`
  （testing 的覆盖优先级更高，盖不住环境变量）。
- **pydantic-settings 优先级**：构造参数 > 环境变量 > dotenv > 模型默认值。
  `_ENV_OVERRIDES` 是构造参数，永远盖得住环境变量——想用环境变量改库地址，
  就要选对应环境覆盖字典为空的那个 APP_ENV。
- **schema 漂移自检**：版本戳在 head 但结构落后时，`alembic stamp <down_revision>`
  再 `upgrade head` 即可修复（迁移 upgrade 幂等）；修复后用
  `SQLModel.metadata` ↔ `PRAGMA table_info` 全表核对确认。
