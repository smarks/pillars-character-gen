#!/bin/bash
#
# Pillars Character Generator - Deployment Script
#
# Usage:
#   ./deploy.sh          # Full deploy (install deps, migrate, restart)
#   ./deploy.sh quick    # Quick deploy (just restart, no migrations)
#
# Prerequisites:
#   1. Create .env file with required variables (see .env.example)
#   2. Set up systemd service (see pillars.service)
#   3. Configure nginx as reverse proxy
#
set -e

# Configuration
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/.venv"
WEBAPP_DIR="$APP_DIR/webapp"
SERVICE_NAME="pillars"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment variables
if [ -f "$APP_DIR/.env" ]; then
    log_info "Loading environment from .env"
    set -a
    source "$APP_DIR/.env"
    set +a
else
    log_error ".env file not found! Copy .env.example to .env and configure it."
    exit 1
fi

# Check required environment variables
check_env() {
    local missing=0
    for var in DJANGO_SECRET_KEY PILLARS_ADMIN_PASSWORD PILLARS_DM_PASSWORD; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            missing=1
        fi
    done
    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

# Create/update virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi

    log_info "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    log_info "Installing/updating dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet -r "$APP_DIR/requirements.txt"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    cd "$WEBAPP_DIR"
    python manage.py migrate --noinput
}

# Create default users
create_users() {
    log_info "Creating/updating default users..."
    cd "$WEBAPP_DIR"
    python manage.py create_default_users
}

# Collect static files
collect_static() {
    log_info "Collecting static files..."
    cd "$WEBAPP_DIR"
    python manage.py collectstatic --noinput --clear 2>/dev/null || true
}

# Restart the service
restart_service() {
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        log_info "Restarting $SERVICE_NAME service..."
        sudo systemctl restart "$SERVICE_NAME"
    else
        log_warn "Service $SERVICE_NAME not found or not running. Start manually with:"
        echo "  sudo systemctl start $SERVICE_NAME"
    fi

    # Reload nginx if running (for reverse proxy)
    if systemctl is-active --quiet "nginx" 2>/dev/null; then
        log_info "Reloading nginx..."
        sudo systemctl reload nginx
    fi
}

# Check service status
check_status() {
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        log_info "Service $SERVICE_NAME is running"
        systemctl status "$SERVICE_NAME" --no-pager | head -5
    else
        log_warn "Service $SERVICE_NAME is not running"
    fi
}

# Main deployment
main() {
    log_info "Starting deployment..."

    check_env

    if [ "$1" != "quick" ]; then
        setup_venv
        run_migrations
        create_users
        collect_static
    else
        log_info "Quick deploy - skipping setup steps"
        source "$VENV_DIR/bin/activate"
    fi

    restart_service
    check_status

    log_info "Deployment complete!"
}

main "$@"
