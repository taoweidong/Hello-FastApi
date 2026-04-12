# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Project Overview

Hello-FastApi is a full-stack admin system with a FastAPI backend (`service/`) and a Vue3 frontend (`web/`). The backend uses Domain-Driven Design (DDD) and RBAC authentication; the frontend uses Pure Admin as its base template.

---

## Backend (`service/`)

### Setup & Development

```bash
cd service

# Create virtual environment (Python 3.10 required)
uv venv --python 3.10
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# Install all dependencies (including dev)
uv pip install -e ".[dev]"

# Initialize the database and seed default data
python -m scripts.cli initdb
python -m scripts.cli seedrbac
python -m scripts.cli createsuperuser -u admin -e admin@example.com -p admin123

# Run development server (http://localhost:8000)
python -m scripts.cli runserver
# Swagger UI: http://localhost:8000/api/docs
```

Environment is controlled by `APP_ENV` (development/production/testing). Config files: `.env.development`, `.env.production`, `.env.testing`.

### Testing

```bash
cd service

pytest                                          # All tests
pytest tests/unit/                              # Unit tests only
pytest tests/integration/                       # Integration tests only
pytest tests/unit/test_auth.py                  # Single test file
pytest tests/unit/test_auth.py::test_login      # Single test case
pytest --cov=src --cov-report=term-missing      # With coverage
```

Tests use SQLite (in-memory or file) via `.env.testing`. Integration tests hit real HTTP endpoints.

### Linting & Formatting

```bash
ruff check . --fix    # Lint and auto-fix
ruff format .         # Format code
mypy src/             # Type checking
```

Ruff config is in `pyproject.toml`. Line length is 320. All code comments are in Chinese.

---

## Frontend (`web/`)

### Setup & Development

```bash
cd web
pnpm install
pnpm dev        # Dev server at http://localhost:8848
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`. Both services must run simultaneously for full-stack development.

### Build & Lint

```bash
pnpm build          # Production build
pnpm build:staging  # Staging build
pnpm preview        # Preview production build locally
pnpm lint           # ESLint + Prettier + Stylelint
pnpm typecheck      # TypeScript type check (vue-tsc)
```

---

## Architecture

### Backend DDD Layers

```
service/src/
├── api/v1/             # HTTP layer — routers using classy_fastapi.Routable
│   └── dependencies/   # FastAPI Depends() factories for service injection
├── application/
│   ├── dto/            # Request/response data transfer objects (Pydantic)
│   └── services/       # Application services — orchestrate domain objects
├── domain/
│   ├── entities/       # Core business logic (immutable domain models)
│   ├── repositories/   # Abstract interfaces (ABCs) for data access
│   ├── services/       # Domain services: token_service, password_service
│   └── exceptions.py   # Custom business exceptions
├── infrastructure/
│   ├── database/
│   │   ├── models/     # SQLModel ORM models (tables prefixed sys_)
│   │   └── database_manager.py
│   ├── repositories/   # Concrete repository implementations (FastCRUD)
│   └── cache/          # Redis manager
└── config/
    ├── settings.py     # Pydantic-settings multi-env config
    └── asgi.py         # App factory (create_app)
```

**Key principle**: Domain layer has zero infrastructure imports. Application services depend only on domain interfaces, injected at the API layer via `Depends()`.

### Authentication Flow

1. `POST /api/system/login` → `AuthService.login()` → validates credentials, returns JWT access + refresh tokens
2. Subsequent requests: `Authorization: Bearer <access_token>`
3. `get_current_user_id()` dependency extracts and validates the token
4. `require_permission("code")` dependency checks user roles/permissions
5. Superusers (`is_superuser=1`) bypass all permission checks

**Dual-token**: access token (30 min) + refresh token (7 days). Token logic is in `domain/services/token_service.py`.

### RBAC Model

User → Role (many-to-many) → Menu/Permission (many-to-many). Menu entries also define frontend routes returned dynamically by `/api/system/router`.

### API Response Format

All endpoints return a unified structure:

```json
{ "code": 0, "message": "操作成功", "data": {} }
```

Paginated responses wrap data as `{ "list": [], "total": 0, "pageSize": 10, "currentPage": 1 }`.

### Frontend Architecture

```
web/src/
├── api/            # Axios calls grouped by domain (system/user.ts, etc.)
├── store/          # Pinia modules: user, permission, app, multiTags, settings
├── router/         # Vue Router; dynamic routes built from backend menu API
├── views/          # Page components by domain (system/, dashboard/, login/)
├── components/     # Shared components: ReAuth, RePerms (permission-gated rendering)
├── utils/http.ts   # Axios instance with auth interceptors and token refresh
└── layout/         # App shell (nav, sidebar, tabs)
```

Dynamic routing: on login, the frontend fetches `/api/system/router`, converts the menu tree into Vue Router routes, and adds them at runtime. The `permission.ts` store owns this lifecycle.

### Database

All tables are prefixed `sys_`. Primary keys are 32-char UUID strings. Key tables: `sys_users`, `sys_roles`, `sys_menus`, `sys_permissions`, `sys_departments`, `sys_user_roles`, `sys_role_menus`, `sys_login_logs`, `sys_operation_logs`, `sys_ip_rules`, `sys_system_config`.

### Docker

```bash
cd service/docker
docker-compose up -d
docker-compose exec app python -m scripts.cli initdb
docker-compose exec app python -m scripts.cli seedrbac
docker-compose exec app python -m scripts.cli createsuperuser
```

Backend image: `python:3.10-slim`, runs uvicorn with 4 workers on port 8000.
