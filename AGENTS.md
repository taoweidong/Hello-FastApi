# AGENTS.md

Monorepo: FastAPI backend (`service/`) + Vue3 frontend (`web/`).
Frontend scaffolded from **vue-pure-admin v7**; backend ports pure-admin-backend from Java to Python.

## Backend (service/)

**Setup** (requires Python >= 3.10, `uv`):
```bash
uv venv --python 3.10
.venv\Scripts\activate              # Windows
source .venv/bin/activate           # Linux/Mac
uv pip install -e ".[dev]"
```

**CLI commands** (run from `service/`, all via `python -m scripts.cli <cmd>`):
| Command | Purpose |
|---|---|
| `runserver` | Dev server on port 8000 (host/port from `settings`) |
| `initall` | One-shot: `initdb` → `seeddata` → `seedrbac` → `createsuperuser` |
| `initdb` | Runs **Alembic** `upgrade head` (not `create_all`) |
| `seeddata` | Test data (operation/login logs) |
| `seedrbac` | Default menus + roles. **Must run after `seeddata`** |
| `createsuperuser -u <name> -e <email> -p <pwd>` | Superuser with `admin` role |
| `migrate` | Alias for `alembic upgrade head` |
| `rollback --steps N` | `alembic downgrade -N` |
| `stamp <rev>` | `alembic stamp <rev>` (mark version without running SQL) |

Default superuser: `admin` / `admin123` (after `initall`).

**Tests:**
```bash
pytest                                  # ~1828 tests
pytest tests/unit/                      # unit only
pytest tests/integration/               # integration only
pytest -n auto                          # parallel (xdist; safe — each worker gets a temp-file SQLite DB)
pytest -k <pattern>                     # single test or module
pytest --cov=src --cov-report=term-missing
ruff check src/ --fix && ruff format src/   # lint + format (line-length=120)
mypy src/                               # typecheck
```

**Architecture** — DDD 4-layer under `src/`: `api/` → `application/` → `domain/` → `infrastructure/`.
- `src/api/v1/` — routers (classy-fastapi): `auth`, `user`, `role`, `menu`, `dept`, `dictionary`, `log`, `monitor`, `system_config`, `ip_rule`. Aggregated in `src/api/v1/__init__.py`.
- `src/api/dependencies/` — one `Depends` provider per service.
- `src/application/services/` — use cases (one per domain); transaction control lives here.
- `src/application/mappers/` — DTO ↔ entity ↔ dict mappers.
- `src/domain/entities/`, `src/domain/repositories/` (interfaces), `src/domain/services/` (`CachePort`, `IPFilterPort`, `LoggingPort`, `PasswordService`, `TokenService`).
- `src/infrastructure/repositories/` — SQLModel impls with `to_domain()` / `from_domain()`.
- `src/infrastructure/cache/` — Redis cache with auto-degradation.
- `src/infrastructure/http/` — middleware: CORS, IP filter, rate limit (SlowAPI), request logging.
- `src/infrastructure/database/models/` — SQLModel table definitions imported by Alembic env and by `tests/conftest.py` (`autouse setup_database`).

**API prefix:** `/api/system` (`src/api/constants.py`). Docs at `/docs`, `/redoc`, `/openapi.json`.

**Database:** SQLite for dev (`sql/dev.db`) and test (`sql/test.db`); PostgreSQL for production. Redis for cache + rate-limit. Migrations via **Alembic** (`alembic/`, `alembic.ini`) — do not use `create_all` outside tests.

**Test fixtures** (`tests/conftest.py`):
- `client` — `httpx.AsyncClient` over `ASGITransport(test_app)`, `get_db` overridden per-test.
- `test_app` — built with `empty_lifespan` so the real DB init does not run.
- `setup_database` (autouse) — `create_all` before each test, `drop_all` after.
- `db_session` — async session bound to the test engine.
- `auth_headers` — auto-creates a superuser and yields `{"Authorization": "Bearer <jwt>"}`.
- `test_user_data` — sample user-create dict.
- `os.environ.setdefault("APP_ENV", "testing")` runs at import time so `Settings` picks up `.env.testing`.

**Lint (ruff):** `line-length=120`, `select = E,F,W,I,N,UP,B,A,SIM`, `ignore = B008`, `skip-magic-trailing-comma = true`. Per-file ignores: `N803` + `N815` in `src/api/`, `N815` in `src/application/dto/` (frontend uses camelCase JSON, so PEP8 is intentionally violated for DTO field names).

**Smoke test:** `service/tests/ui_test.py` — Playwright full-stack script (login + page nav + API). Requires both servers running; writes screenshots to `tests/screenshots/`. Not in CI.

## Frontend (web/)

**Constraints:** `pnpm >= 9`, Node `^20.19.0 || >=22.13.0`. The `preinstall` script (`only-allow pnpm`) blocks `npm`/`yarn` — do not try to install with them.

**Commands:**
```bash
pnpm install
pnpm dev                  # port 8848 (VITE_PORT in .env.development)
pnpm lint                 # eslint + prettier + stylelint (eslint uses --max-warnings 0)
pnpm typecheck            # vue-tsc --noEmit --skipLibCheck
pnpm build                # production
pnpm build:staging        # staging mode
pnpm test:e2e             # Playwright (requires backend + frontend running)
pnpm test:e2e:headed      # headed mode
```

**Proxy:** Vite proxies `/api` → `http://localhost:8000` (`vite.config.ts`). Start backend first for full-stack dev.

**Architecture** — vue-pure-admin v7 conventions:
- `src/api/system.ts` → `BaseApi` subclass; `BaseApi` (in `src/api/base.ts`) provides `list/retrieve/create/partialUpdate/destroy/batchDelete` for all CRUD modules. Per-module files under `src/api/system/`.
- `src/router/` — routes are **fetched from backend after login** (dynamic), not statically defined.
- `src/views/` — pages mirror backend routers 1:1.
- `e2e/` — Playwright tests; sample at `e2e/login.spec.ts` (uses default `admin` / `admin123`).
- `mock/` — `vite-plugin-fake-server` for dev mocks. Real backend calls go to `/api/system/*`.
- Stack: Vue 3.5 + TypeScript 6 + Element Plus + Pinia 3 + Vite 8 (Rolldown/Oxc) + Tailwind 4.

## Full-stack Dev

1. `cd service && python -m scripts.cli runserver`  → http://localhost:8000
2. `cd web && pnpm dev`  → http://localhost:8848
3. API docs: http://localhost:8000/docs
4. Default login: `admin` / `admin123`

## Verification Flow

**Backend:** `ruff check src/ && ruff format src/ --check && mypy src/ && pytest`
**Frontend:** `pnpm lint && pnpm typecheck`
**Full-stack e2e:**
```bash
# Terminal 1
cd service && python -m scripts.cli runserver &
# Terminal 2
cd web && pnpm dev &
# Terminal 3
cd web && pnpm test:e2e
```
Backend smoke: `cd service && python -m tests.ui_test` (also requires both servers).

Pre-push hooks: husky + lint-staged (configured in `web/`). Jenkinsfile in `service/` mirrors the lint/format/typecheck/test pipeline with `--cov-fail-under=95`.

## Docker

```bash
cd service/docker && docker-compose up -d
docker-compose exec app python -m scripts.cli initall
```
Standalone FastAPI + PostgreSQL 15 + Redis 7. Uses `APP_ENV=production` and a `/health` endpoint for healthchecks.

## Settings & Env

- Active env: `APP_ENV` env var or `.env` file. Files: `.env.development`, `.env.production`, `.env.testing`.
- Resolution order: constructor kwargs > `.env.{APP_ENV}` > `.env` > model defaults.
- Settings are singleton via `get_settings()` / `get_cached_settings()` (`lru_cache`). Access the singleton as `from src.config.settings import settings`.
- Profile defaults (`settings.py`): `production` → `DEBUG=False`, `LOG_LEVEL=WARNING`; `testing` → `DEBUG=True`, `LOG_LEVEL=DEBUG`, `DATABASE_URL=sqlite+aiosqlite:///./sql/test.db`.

## CodeGraph Integration

**CodeGraph** is configured as the primary code search tool. When searching for symbols, functions, callers, callees, or impact analysis, **always prefer CodeGraph MCP tools** over built-in grep/glob:

| Tool | Use case |
|---|---|
| `codegraph_search` | Find symbols by name/signature/docstring (FTS5 full-text search) |
| `codegraph_node` | Look up a symbol by ID or exact name |
| `codegraph_callers` | Find all functions/methods that call a specific symbol |
| `codegraph_callees` | Find all functions/methods that a specific symbol calls |
| `codegraph_impact` | Transitive impact radius (callers + references) |
| `codegraph_context` | Composed context for a symbol or topic |
| `codegraph_files` | List indexed files under a path |

**Workflow:**
1. For code search → use `codegraph_search` first
2. For understanding call chains → use `codegraph_callers` / `codegraph_callees`
3. For impact analysis before refactoring → use `codegraph_impact`
4. Fall back to `grep`/`glob` only when CodeGraph tools don't cover the need

Index is at `.codegraph/codegraph.db`. Refresh with `codegraph sync` after large changes.

## OpenCode Integration

- **Project skills** in `.opencode/skills/`: `agent-browser`, `code-gen` (MySQL → DDD 4-layer + Vue3 CRUD codegen), `commit-changelog`, `git-release`.
- **agent-browser** — Rust-based headless browser CLI; available globally and as a project skill.
- **Playwright MCP** server (`@playwright/mcp`) configured in `~/.config/opencode/opencode.json` — use the MCP browser tools for in-session automation.
- **CodeGraph MCP** server configured in `opencode.json` — provides semantic code search, call graph, and impact analysis tools.
- **Frontend e2e** uses `@playwright/test` (see `web/playwright.config.ts`).
