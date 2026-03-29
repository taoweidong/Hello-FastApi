#!/bin/bash
# Development environment setup script

set -e

echo "=== Hello-FastApi Development Setup ==="

# 1. Check UV
if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
echo "UV version: $(uv --version)"

# 2. Create virtual environment
echo "Creating virtual environment..."
uv venv --python 3.10

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
echo "Installing dependencies..."
uv pip install -e ".[dev]"

# 5. Run code formatting
echo "Running code formatting..."
ruff format .
ruff check . --fix || true

# 6. Initialize database
echo "Initializing database..."
python manage.py initdb

# 7. Seed RBAC data
echo "Seeding RBAC data..."
python manage.py seedrbac

# 8. Run tests
echo "Running tests..."
pytest -v || true

echo ""
echo "=== Setup Complete ==="
echo "Run 'python manage.py runserver' to start the server"
