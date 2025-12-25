#!/bin/bash
# Development workflow script - common development tasks
# Usage: ./dev.sh [command]

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

COMMAND="${1:-help}"

case "$COMMAND" in
    run|server|start)
        echo "Starting development server..."
        cd webapp
        python manage.py runserver "${@:2}"
        ;;
    test)
        echo "Running tests..."
        shift
        "$SCRIPT_DIR/test.sh" "$@"
        ;;
    e2e)
        echo "Running E2E tests..."
        shift
        "$SCRIPT_DIR/e2e.sh" "$@"
        ;;
    lint)
        echo "Checking code quality..."
        shift
        "$SCRIPT_DIR/lint.sh" "$@"
        ;;
    migrate)
        echo "Running database migrations..."
        cd webapp
        python manage.py makemigrations
        python manage.py migrate
        cd ..
        echo "Migrations complete!"
        ;;
    shell)
        echo "Opening Django shell..."
        cd webapp
        python manage.py shell
        ;;
    createsuperuser)
        echo "Creating Django superuser..."
        cd webapp
        python manage.py createsuperuser
        ;;
    clean)
        echo "Cleaning Python cache files..."
        find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
        echo "Cleanup complete!"
        ;;
    install)
        echo "Installing/updating dependencies..."
        uv pip install -r requirements.txt
        echo "Dependencies installed!"
        ;;
    setup)
        echo "Running full setup..."
        "$SCRIPT_DIR/setup.sh"
        ;;
    help|*)
        echo "Pillars Character Generator - Development Workflow"
        echo ""
        echo "Usage: ./dev.sh [command]"
        echo ""
        echo "Commands:"
        echo "  run, server, start    Start the Django development server"
        echo "  test [type]           Run tests (all|core|webapp|pattern)"
        echo "  lint [action]         Check/fix code quality (check|format|fix)"
        echo "  migrate               Create and apply database migrations"
        echo "  shell                 Open Django shell"
        echo "  createsuperuser       Create Django superuser"
        echo "  clean                 Remove Python cache files"
        echo "  install               Install/update dependencies"
        echo "  setup                 Run full project setup"
        echo "  help                  Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./dev.sh run                    # Start server"
        echo "  ./dev.sh test core              # Run core tests only"
        echo "  ./dev.sh lint format            # Format code"
        echo "  ./dev.sh migrate                # Run migrations"
        ;;
esac

