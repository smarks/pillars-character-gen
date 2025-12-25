#!/bin/bash
# Database management script for Pillars Character Generator

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

# Load environment variables
load_env_with_fallback

# Activate virtual environment
source .venv/bin/activate

cd webapp

COMMAND="${1:-help}"

case "$COMMAND" in
    migrate|migrate-apply)
        echo "Applying database migrations..."
        python manage.py migrate
        echo "Migrations applied!"
        ;;
    makemigrations|create)
        echo "Creating new migrations..."
        python manage.py makemigrations
        echo "Migrations created! Review and apply with: ./db.sh migrate"
        ;;
    reset)
        echo "⚠️  WARNING: This will delete the database and recreate it!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "Removing database..."
            rm -f db.sqlite3
            echo "Creating new database..."
            python manage.py migrate
            python manage.py create_default_users
            echo "Database reset complete!"
        else
            echo "Cancelled."
        fi
        ;;
    shell)
        echo "Opening Django database shell..."
        python manage.py dbshell
        ;;
    showmigrations)
        echo "Showing migration status..."
        python manage.py showmigrations
        ;;
    sqlmigrate)
        if [ -z "$2" ]; then
            echo "Usage: ./db.sh sqlmigrate <app_name> <migration_number>"
            echo "Example: ./db.sh sqlmigrate generator 0001"
            exit 1
        fi
        echo "Showing SQL for migration: $2"
        python manage.py sqlmigrate "$2" "$3"
        ;;
    help|*)
        echo "Database Management - Pillars Character Generator"
        echo ""
        echo "Usage: ./db.sh [command]"
        echo ""
        echo "Commands:"
        echo "  migrate, migrate-apply    Apply pending migrations"
        echo "  makemigrations, create    Create new migrations"
        echo "  reset                    Reset database (⚠️  deletes data!)"
        echo "  shell                    Open database shell"
        echo "  showmigrations           Show migration status"
        echo "  sqlmigrate <app> <num>   Show SQL for a migration"
        echo "  help                     Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./db.sh migrate                    # Apply migrations"
        echo "  ./db.sh makemigrations             # Create migrations"
        echo "  ./db.sh showmigrations             # Check status"
        ;;
esac

