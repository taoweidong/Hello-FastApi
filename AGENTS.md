# AGENTS.md

Monorepo: FastAPI backend (`service/`) + Vue3 frontend (`web/`).

## Backend (service/)

**Setup:**
```bash
uv venv --python 3.10
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
uv pip install -e ".[dev]"
```

**Commands:**
```bash
python -m scripts.cli runserver            # Dev server (port 8000)
python -m scripts.cli initdb               # Create tables
python -m scripts.cli seeddata             # Test menu/log seed data
python -m scripts.cli seedrbac             # Role/permission defaults (AFTER seeddata)
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
python -m scripts.cli initall              # One-click: all above in correct order
pytest                                     # All tests (~1828)
pytest tests/unit/                         # Unit tests only
pytest tests/integration/                  # Integration tests only
pytest -n auto                             # Parallel with xdist
pytest --cov=src --cov-report=term-missing  # Coverage
ruff check src/ --fix && ruff format src/  # Lint + format
mypy src/                                  # Typecheck
```

**Architecture:** DDD 4-layer — `api/` → `application/` → `domain/` → `infrastructure/`.
- `src/api/v1/` — routers (auth, user, role, menu, dept, dict, log, monitor, system_config, ip_rule)
- `src/api/dependencies/` — FastAPI `Depends` injection (one file per service)
- `src/application/services/` — use cases, transaction control
- `src/domain/entities/`, `src/domain/repositories/` — abstract interfaces
- `src/infrastructure/repositories/` — SQLModel implementations with `to_domain()`/`from_domain()`
- `src/infrastructure/cache/` — Redis cache with auto-degradation
- `src/infrastructure/http/` — middleware (CORS, IP filter, rate limit, request logging)
- `src/config/settings.py` — multi-env config via `get_settings()` singleton

**API prefix:** `/api/system` (defined in `src/api/constants.py`).

**Database:** SQLite for dev (`sql/dev.db`), PostgreSQL for production. Redis for cache+rate-limit.
Alembic for migrations. Init order matters: `initdb → seeddata → seedrbac → createsuperuser`.

**Testing fixtures** (from `tests/conftest.py`):
- `client` — `httpx.AsyncClient` wired to test app via `ASGITransport` (in-memory SQLite)
- `db_session` — test DB session (table create/drop per test via `setup_database` autouse)
- `auth_headers` — auto-creates superuser + JWT token
- `test_user_data` — sample user creation dict
- xdist-compatible: each worker gets an isolated temp-file DB

**Lint (ruff):** `line-length=120`, per-file-ignores: `N803`, `N815` in `api/` and `dto/` (camelCase for JSON fields).

**Known DIP violations (P1):** `IPRuleService`, `MenuService`, `UserService` directly import `infrastructure.cache` concrete classes instead of domain-level `CachePort`.

**Existing UI test** at `service/tests/ui_test.py` — Playwright-based full-stack test (login, page navigation, API endpoints). Requires both servers running. Not in CI.

**API docs:** `/docs` (Swagger), `/redoc` (ReDoc), `/openapi.json`.

## Frontend (web/)

**Constraints:** `pnpm >= 9`. Node.js: `^20.19.0 || >=22.13.0`. Preinstall script blocks npm/yarn.

**Commands:**
```bash
pnpm install
pnpm dev                     # Dev server (port 8848)
pnpm lint                    # ESLint + Prettier + Stylelint
pnpm typecheck               # vue-tsc
pnpm build
pnpm build:staging           # Build with staging mode
pnpm test:e2e                # Playwright e2e tests (requires servers running)
pnpm test:e2e:headed         # Playwright e2e in headed mode
```

**Proxy:** Vite proxies `/api` → `localhost:8000`. Start backend before frontend for full-stack dev.

**Architecture:** Pure Admin (vue-pure-admin) scaffold. Key dirs:
- `src/api/` — `BaseApi` class provides `list/retrieve/create/partialUpdate/destroy/batchDelete` for all CRUD modules
- `src/router/` — dynamic routes fetched from backend after login
- `src/store/` — Pinia stores
- `src/views/` — page components matching backend routers
- `e2e/` — Playwright e2e tests (requires both servers running)

**Mock:** Uses `vite-plugin-fake-server` for dev mock data. Real backend calls go to `/api/system/*`.

## Full-stack Dev

1. Start backend: `cd service && python -m scripts.cli runserver`
2. Start frontend: `cd web && pnpm dev`
3. Frontend: http://localhost:8848, Backend: http://localhost:8000
4. API docs: http://localhost:8000/docs
5. Default login: `admin` / `admin123`

## Verification Flow

**Backend:** `ruff check src/ && ruff format src/ && mypy src/ && pytest`
**Frontend:** `pnpm lint && pnpm typecheck`
**Full-stack e2e (2 ways):**

1. **Frontend Playwright** (recommended for CI):
   ```bash
   # Terminal 1: start backend + frontend
   cd service && python -m scripts.cli runserver &
   cd web && pnpm dev &
   # Terminal 2: run e2e tests
   cd web && pnpm test:e2e
   ```

2. **Backend Playwright script** (smoke test):
   ```bash
   cd service && source .venv_linux/bin/activate && python -m tests.ui_test
   ```
   Requires both servers running. Not in CI.

**Frontend lint expects zero warnings** (`--max-warnings 0` in ESLint). Pre-push hooks via husky + lint-staged.

## Docker

```bash
cd service/docker && docker-compose up -d
docker-compose exec app python -m scripts.cli initall
```
Standalone FastAPI container + PostgreSQL + Redis.

## OpenCode Integration

- **Project skills** in `.opencode/skills/`: `agent-browser` (browser automation CLI), `code-gen` (MySQL→CRUD codegen), `commit-changelog`, `git-release`
- **agent-browser CLI** (v0.25.3) globally available for quick browser interactions.
- **Playwright MCP Server** configured in `~/.config/opencode/opencode.json` (`@playwright/mcp`) — AI can directly control browser via MCP tools.
- **Playwright (MCP) skill** available for browser automation tasks.
- **Frontend e2e**: `@playwright/test` (v1.60) in `web/` with `playwright.config.ts` and sample `e2e/login.spec.ts`.

## Settings & Env

- Environment auto-detected via `APP_ENV` env var or `.env` file
- Config files: `.env.development` (dev), `.env.production` (prod), `.env.testing` (test)
- Priority: constructor kwargs > `.env.{APP_ENV}` > `.env` > model defaults
- Settings are singleton via `get_settings()` / `get_cached_settings()` (lru_cache)
- Testing automatically sets `APP_ENV=testing` in `conftest.py` via `os.environ.setdefault`
