@echo off
REM Development environment setup script for Windows

echo === Hello-FastApi Development Setup ===

REM 1. Check UV
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo Installing UV...
    powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"
)

REM 2. Create virtual environment
echo Creating virtual environment...
uv venv --python 3.10

REM 3. Activate virtual environment
call .venv\Scripts\activate.bat

REM 4. Install dependencies
echo Installing dependencies...
uv pip install -e ".[dev]"

REM 5. Run code formatting
echo Running code formatting...
ruff format .
ruff check . --fix

REM 6. Initialize database
echo Initializing database...
python manage.py initdb

REM 7. Seed RBAC data
echo Seeding RBAC data...
python manage.py seedrbac

REM 8. Run tests
echo Running tests...
pytest -v

echo.
echo === Setup Complete ===
echo Run 'python manage.py runserver' to start the server
