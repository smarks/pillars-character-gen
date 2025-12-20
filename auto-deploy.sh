#!/bin/bash
# Auto-deploy script for Pillars Character Generator
# Checks for git changes, pulls them, runs migrations, and restarts the service

set -e

cd /home/sam/dev/pillars-character-gen

echo "Fetching from origin..."
git fetch

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "Already up to date. No deployment needed."
    exit 0
fi

echo "Changes detected!"
echo "Local:  $LOCAL"
echo "Remote: $REMOTE"

echo ""
echo "Pulling changes..."
git pull

echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

echo ""
echo "Running migrations..."
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db python webapp/manage.py migrate

echo ""
echo "Updating systemd service file..."
sudo cp pillars.service /etc/systemd/system/pillars.service
sudo systemctl daemon-reload

echo ""
echo "Restarting service..."
sudo systemctl restart pillars

echo ""
echo "Deployment complete!"
systemctl status pillars --no-pager
