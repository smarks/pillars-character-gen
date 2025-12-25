#!/bin/bash
# Common functions for Pillars Character Generator scripts

# Load environment variables from .env with PostgreSQL fallback to SQLite
load_env_with_fallback() {
    if [ -f ".env" ]; then
        # Export variables from .env, excluding comments and empty lines
        export $(grep -v '^#' .env | grep -v '^$' | xargs)
        
        # If DATABASE_URL is set but PostgreSQL isn't available, use SQLite instead
        if [ -n "$DATABASE_URL" ]; then
            # Try to connect to PostgreSQL (quick check)
            if command -v psql >/dev/null 2>&1; then
                # Check if we can connect (this is a quick check, may not be perfect)
                if ! psql "$DATABASE_URL" -c "SELECT 1;" >/dev/null 2>&1; then
                    echo "Warning: DATABASE_URL is set but PostgreSQL connection failed."
                    echo "Using SQLite for local development instead."
                    unset DATABASE_URL
                fi
            else
                # psql not available, assume PostgreSQL isn't running
                echo "Note: Using SQLite for local development (PostgreSQL not available)."
                unset DATABASE_URL
            fi
        fi
    fi
}

