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
python -m scripts.cli runserver      # Dev server (port 8000)
python -m scripts.cli initdb         # Create tables
python -m scripts.cli seedrbac       # Menu/role/permission defaults
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123
python -m scripts.cli initall        # One-click init (all above)
pytest                               # Run tests
ruff check src/ --fix && ruff format src/  # Lint + format
mypy src/                            # Typecheck
```

**Architecture:** DDD 4-layer: `api/` → `application/` → `domain/` → `infrastructure/`. API prefix `/api/system`.

**Database:** SQLite for dev (`sql/dev.db`), PostgreSQL for production. Redis optional in dev.

**Testing:** pytest with `asyncio_mode=auto`. Integration tests in `tests/integration/`, unit in `tests/unit/`.

## Frontend (web/)

**Constraints:** Must use `pnpm >= 9`. Node.js: `^20.19.0 || >=22.13.0`. Preinstall script blocks npm/yarn.

**Commands:**
```bash
pnpm install
pnpm dev          # Dev server (port 8848)
pnpm lint         # ESLint + Prettier + Stylelint
pnpm typecheck    # vue-tsc
pnpm build
```

**Proxy:** Vite proxies `/api` → `localhost:8000`. Start backend before frontend for full-stack dev.

## Full-stack Dev

1. Start backend: `cd service && python -m scripts.cli runserver`
2. Start frontend: `cd web && pnpm dev`
3. Frontend at http://localhost:8848, backend at http://localhost:8000
4. API docs: http://localhost:8000/docs

## Verification Flow

Backend: `ruff check src/ && ruff format src/ && mypy src/ && pytest`
Frontend: `pnpm lint && pnpm typecheck`

## Docker

`cd service/docker && docker-compose up -d` — standalone FastAPI container. Init DB inside container: `docker-compose exec app python -m scripts.cli initall`