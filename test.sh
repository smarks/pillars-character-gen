#!/bin/bash
# Test runner for Pillars Character Generator
# Supports core library tests, Django webapp tests, and E2E tests

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source common functions
source "$SCRIPT_DIR/scripts/common.sh"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run setup first:"
    echo "  ./setup.sh"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Parse arguments
TEST_TYPE="${1:-all}"  # all, core, webapp, e2e, or specific file
COVERAGE="${2:-false}"  # true or false
COVERAGE_TYPE="${3:-core}"  # core, webapp, or all (for coverage)

case "$TEST_TYPE" in
    core)
        echo "Running core library tests..."
        if [ "$COVERAGE" = "true" ]; then
            python -m pytest tests/ -v --cov=pillars --cov-report=html --cov-report=term-missing
            echo ""
            echo "Coverage report generated in htmlcov/index.html"
        else
            python -m pytest tests/ -v
        fi
        ;;
    webapp)
        echo "Running Django webapp tests..."
        cd webapp
        if [ "$COVERAGE" = "true" ]; then
            python manage.py test --keepdb
            # Django test coverage requires different approach
            coverage run --source='.' manage.py test
            coverage report
            coverage html
            echo ""
            echo "Coverage report generated in htmlcov/index.html"
        else
            python manage.py test
        fi
        cd ..
        ;;
    e2e)
        echo "Running E2E (Selenium) tests..."
        echo "Note: This requires Chrome/Chromium to be installed"
        cd webapp
        python manage.py test webapp.generator.ui_tests --keepdb
        cd ..
        ;;
    all)
        echo "Running all tests..."
        echo ""
        echo "=== Core Library Tests ==="
        python -m pytest tests/ -v
        echo ""
        echo "=== Django Webapp Tests ==="
        cd webapp
        python manage.py test --keepdb
        cd ..
        
        if [ "$COVERAGE" = "true" ]; then
            echo ""
            echo "=== Generating Coverage Report ==="
            # Core library coverage
            python -m pytest tests/ --cov=pillars --cov-report=term-missing --cov-report=html:htmlcov/core || true
            # Webapp coverage (Django tests)
            cd webapp
            coverage run --source='webapp' manage.py test --keepdb || true
            coverage report || true
            coverage html -d ../htmlcov/webapp || true
            cd ..
            echo ""
            echo "Coverage reports generated:"
            echo "  - Core library: htmlcov/core/index.html"
            echo "  - Webapp: htmlcov/webapp/index.html"
        fi
        ;;
    *)
        # Assume it's a specific test file or pattern
        if [ -f "$TEST_TYPE" ]; then
            echo "Running specific test file: $TEST_TYPE"
            if [ "$COVERAGE" = "true" ]; then
                python -m pytest "$TEST_TYPE" -v --cov=pillars --cov-report=term-missing
            else
                python -m pytest "$TEST_TYPE" -v
            fi
        else
            echo "Running tests matching pattern: $TEST_TYPE"
            if [ "$COVERAGE" = "true" ]; then
                python -m pytest tests/ -v -k "$TEST_TYPE" --cov=pillars --cov-report=term-missing
            else
                python -m pytest tests/ -v -k "$TEST_TYPE"
            fi
        fi
        ;;
esac

echo ""
echo "Tests completed!"

