#!/bin/bash
# Code quality and formatting script for Pillars Character Generator
# Checks code style, formats code, and runs basic linting

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run setup first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if tools are installed, install if needed
install_if_missing() {
    if ! python -m "$1" --version >/dev/null 2>&1; then
        echo "Installing $1..."
        uv pip install "$1"
    fi
}

# Install formatting/linting tools if not present
install_if_missing black
install_if_missing ruff
install_if_missing mypy 2>/dev/null || echo "Note: mypy optional, skipping..."

ACTION="${1:-check}"  # check, format, or fix

case "$ACTION" in
    format)
        echo "Formatting code with black..."
        python -m black pillars/ tests/ webapp/ --exclude migrations
        echo "Code formatted!"
        ;;
    fix)
        echo "Fixing code issues with ruff..."
        python -m ruff check --fix pillars/ tests/ webapp/ --exclude migrations
        echo "Running black formatter..."
        python -m black pillars/ tests/ webapp/ --exclude migrations
        echo "Code fixed and formatted!"
        ;;
    check|*)
        echo "Checking code quality..."
        echo ""
        echo "=== Black formatting check ==="
        python -m black --check pillars/ tests/ webapp/ --exclude migrations || echo "⚠️  Some files need formatting (run ./lint.sh format)"
        echo ""
        echo "=== Ruff linting ==="
        python -m ruff check pillars/ tests/ webapp/ --exclude migrations || echo "⚠️  Some issues found (run ./lint.sh fix)"
        echo ""
        echo "Code quality check completed!"
        ;;
esac

