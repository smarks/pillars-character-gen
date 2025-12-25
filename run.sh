#!/bin/bash
# Helper script to run the Pillars Character Generator development server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source common functions
source "$SCRIPT_DIR/scripts/common.sh"

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run setup first:"
    echo "  uv venv"
    echo "  uv pip install -r requirements.txt"
    exit 1
fi

# Load environment variables from .env with PostgreSQL fallback
load_env_with_fallback

# Activate virtual environment
source .venv/bin/activate

# Change to webapp directory
cd webapp

# Run the Django development server
echo "Starting Django development server..."
echo "Open http://127.0.0.1:8000 in your browser"
python manage.py runserver "$@"

