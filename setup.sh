#!/bin/bash
# Setup script for Pillars Character Generator using uv

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source common functions
source "$SCRIPT_DIR/scripts/common.sh"

echo "Setting up Pillars Character Generator..."

# Check if uv is installed
if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
uv venv

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found."
    echo "You may need to create one. See .env.example if available."
else
    echo "Found .env file."
fi

# Load environment variables for database setup with PostgreSQL fallback
load_env_with_fallback

# Activate virtual environment
source .venv/bin/activate

# Run migrations
echo "Running database migrations..."
cd webapp
python manage.py migrate

# Create default users
echo "Creating default users..."
python manage.py create_default_users || echo "Note: Default users may already exist."

echo ""
echo "Setup complete!"
echo ""
echo "To run the development server:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  cd webapp"
echo "  source ../.venv/bin/activate"
echo "  python manage.py runserver"

