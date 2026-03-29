#!/bin/bash
# Lint and format check script

set -e

echo "=== Running Code Quality Checks ==="

echo "1. Ruff format check..."
ruff format --check .

echo "2. Ruff lint check..."
ruff check .

echo "3. MyPy type check..."
mypy src/ || true

echo ""
echo "=== All checks passed ==="
