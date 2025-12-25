# Pillars Character Generator

A Django web application for creating and managing characters for the Pillars tabletop RPG.

## Quick Start

### Using the helper scripts (recommended)

```bash
# First time setup
./setup.sh

# Run the development server
./run.sh
```

Open http://127.0.0.1:8000 in your browser.

### Manual setup

```bash
cd webapp
source ../.venv/bin/activate
python manage.py runserver
```

## Setup From Scratch

### Using uv (recommended)

1. **Install uv** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Create virtual environment and install dependencies:**
   ```bash
   uv venv
   uv pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (or use defaults for local dev)
   ```

4. **Initialize database and run:**
   ```bash
   cd webapp
   source ../.venv/bin/activate
   python manage.py migrate
   python manage.py create_default_users  # creates admin/dm users from .env
   python manage.py runserver
   ```

### Using traditional Python venv

1. **Create virtual environment and install dependencies:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings (or use defaults for local dev)
   ```

3. **Initialize database and run:**
   ```bash
   cd webapp
   python manage.py migrate
   python manage.py create_default_users  # creates admin/dm users from .env
   python manage.py runserver
   ```

## Helper Scripts

- **`setup.sh`** - Complete setup: creates venv, installs dependencies, runs migrations, creates default users
- **`run.sh`** - Runs the development server (loads .env automatically, falls back to SQLite if PostgreSQL unavailable)
- **`dev.sh`** - Development workflow hub (run, test, lint, migrate, etc.)
- **`test.sh`** - Test runner for core library and Django tests
- **`e2e.sh`** - End-to-end (Selenium) browser tests
- **`lint.sh`** - Code quality checks and formatting
- **`db.sh`** - Database management (migrations, reset, etc.)

All scripts automatically handle environment variables and database selection.

## Running Tests

### Quick Test Commands

```bash
# Run all tests (core + webapp)
./test.sh all

# Run only core library tests
./test.sh core

# Run only Django webapp tests
./test.sh webapp

# Run with coverage
./test.sh all true

# Run E2E (browser) tests
./e2e.sh

# Or use the dev workflow
./dev.sh test
./dev.sh e2e
```

### Test Coverage

```bash
# Generate coverage report for core library
./test.sh core true

# Generate coverage report for all tests
./test.sh all true

# View coverage report
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### E2E Testing

E2E tests use Selenium to test the web UI in a real browser:

```bash
# Run all E2E tests (headless)
./e2e.sh

# Run specific test suite
./e2e.sh generator    # Generator UI tests
./e2e.sh role         # Role-based access tests
./e2e.sh session      # Session persistence tests
./e2e.sh login        # Login flow tests

# Run in visible browser (for debugging)
./e2e.sh all false

# Verbose output
./e2e.sh all true 2
```

**Note:** E2E tests require Chrome/Chromium to be installed.

## Configuration

The app uses SQLite by default. See `.env.example` for all configuration options including:
- PostgreSQL database setup
- Production deployment settings (gunicorn, HTTPS)
- Default user credentials

## CI/CD

The project includes GitHub Actions workflows (`.github/workflows/ci.yml`) that:
- Run tests on Python 3.10, 3.11, and 3.12
- Run core library tests, Django tests, and E2E tests
- Check code formatting and linting
- Generate coverage reports
- Test against PostgreSQL database

Tests run automatically on push and pull requests.

## Project Structure

```
character_gen/
├── webapp/           # Django project
│   ├── webapp/       # Main app (settings, urls)
│   │   └── generator/  # Character generator app
│   └── manage.py
├── pillars/          # Core library
├── docs/             # Documentation
├── references/       # Reference materials
├── .github/          # GitHub Actions workflows
│   └── workflows/
│       └── ci.yml    # CI/CD pipeline
├── .coveragerc       # Coverage configuration
└── requirements.txt
```
