#!/bin/bash
# End-to-End (E2E) test runner for Pillars Character Generator
# Runs Selenium-based browser tests

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

# Check if Selenium is installed
if ! python -c "import selenium" 2>/dev/null; then
    echo "Installing Selenium dependencies..."
    uv pip install selenium webdriver-manager
fi

# Check for Chrome/Chromium
if ! command -v google-chrome >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1 && ! command -v chromium-browser >/dev/null 2>&1; then
    # On macOS, check for Chrome in Applications
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if [ ! -d "/Applications/Google Chrome.app" ]; then
            echo "⚠️  Warning: Chrome/Chromium not found in standard locations."
            echo "   E2E tests require Chrome or Chromium to be installed."
            echo "   On macOS, install Chrome from: https://www.google.com/chrome/"
        fi
    else
        echo "⚠️  Warning: Chrome/Chromium not found."
        echo "   E2E tests require Chrome or Chromium to be installed."
    fi
fi

cd webapp

# Parse arguments
TEST_CLASS="${1:-all}"  # all, GeneratorUITests, RoleUITests, etc.
HEADLESS="${2:-true}"  # true or false
VERBOSITY="${3:-1}"    # 0, 1, or 2

# Set headless mode via environment variable
if [ "$HEADLESS" = "false" ]; then
    export SELENIUM_HEADLESS="false"
    echo "Running E2E tests in visible browser mode..."
else
    export SELENIUM_HEADLESS="true"
    echo "Running E2E tests in headless mode..."
fi

case "$TEST_CLASS" in
    all)
        echo "Running all E2E tests..."
        python manage.py test webapp.generator.ui_tests --verbosity=$VERBOSITY --keepdb
        ;;
    generator)
        echo "Running Generator UI tests..."
        python manage.py test webapp.generator.ui_tests.GeneratorUITests --verbosity=$VERBOSITY --keepdb
        ;;
    role)
        echo "Running Role-based access tests..."
        python manage.py test webapp.generator.ui_tests.RoleUITests --verbosity=$VERBOSITY --keepdb
        ;;
    session)
        echo "Running Session persistence tests..."
        python manage.py test webapp.generator.ui_tests.SessionPersistenceTests --verbosity=$VERBOSITY --keepdb
        ;;
    login)
        echo "Running Login flow tests..."
        python manage.py test webapp.generator.ui_tests.SessionCharacterLoginUITests --verbosity=$VERBOSITY --keepdb
        ;;
    interactive)
        echo "Running Interactive flow tests..."
        python manage.py test webapp.generator.ui_tests.InteractiveFlowTests --verbosity=$VERBOSITY --keepdb
        ;;
    combat)
        echo "Running Combat page image tests..."
        python manage.py test webapp.generator.ui_tests.CombatPageImageTests --verbosity=$VERBOSITY --keepdb
        ;;
    *)
        # Try to run as a specific test class or method
        echo "Running specific E2E test: $TEST_CLASS"
        python manage.py test "webapp.generator.ui_tests.$TEST_CLASS" --verbosity=$VERBOSITY --keepdb
        ;;
esac

cd ..

echo ""
echo "E2E tests completed!"

