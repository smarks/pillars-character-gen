# Running GitHub Actions Workflows Locally

This guide explains how to test and run GitHub Actions workflows locally before pushing to GitHub.

## Option 1: Using `act` (Recommended)

`act` is a tool that runs your GitHub Actions workflows locally using Docker.

### Installation

**macOS (using Homebrew):**
```bash
brew install act
```

**Linux:**
```bash
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

**Windows:**
```bash
choco install act-cli
```

Or download from: https://github.com/nektos/act/releases

### Basic Usage

1. **List available workflows:**
   ```bash
   act -l
   ```

2. **Run a specific workflow:**
   ```bash
   # Run the CI workflow
   act push
   
   # Run on a specific event
   act pull_request
   ```

3. **Run a specific job:**
   ```bash
   # Run only the test job
   act -j test
   
   # Run only the lint job
   act -j lint
   ```

4. **Run with specific Python version:**
   ```bash
   # Run test job with Python 3.12
   act -j test --matrix python-version:3.12
   ```

5. **Run with environment variables:**
   ```bash
   act -j test --env DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pillars_test
   ```

### Advanced Usage

**Use a specific Docker image:**
```bash
act -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

**Run in dry-run mode (see what would run):**
```bash
act -n
```

**Run with verbose output:**
```bash
act -v
```

**Run with secrets (create `.secrets` file):**
```bash
# .secrets file
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pillars_test
DJANGO_SECRET_KEY=test-secret-key
```

Then run:
```bash
act --secret-file .secrets
```

### Limitations

- `act` uses Docker, so you need Docker installed and running
- Some GitHub Actions may not work perfectly (especially those that interact with GitHub APIs)
- Service containers (like PostgreSQL) should work, but may need configuration
- Matrix strategies work, but may be slower

## Option 2: Manual Workflow Replication

You can manually replicate the workflow steps locally:

### Test Job Replication

```bash
# 1. Set up environment
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pillars_test
export DJANGO_SECRET_KEY=test-secret-key-for-ci
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# 2. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 3. Set up PostgreSQL (if not already running)
# Using Docker:
docker run -d \
  --name pillars-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=pillars_test \
  -p 5432:5432 \
  postgres:15

# Wait for PostgreSQL to be ready
until pg_isready -h localhost -p 5432 -U postgres; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# 4. Run database migrations
cd webapp
python manage.py migrate

# 5. Run core library tests
cd ..
python -m pytest tests/ -v

# 6. Collect static files
cd webapp
python manage.py collectstatic --noinput --clear
cd ..

# 7. Run Django webapp tests
cd webapp
python manage.py test --keepdb
cd ..

# 8. Run E2E tests (requires Chrome/Chromium and xvfb)
# Install system dependencies first:
# macOS: brew install chromedriver xvfb
# Linux: sudo apt-get install chromium-browser xvfb
cd webapp
xvfb-run -a python manage.py test webapp.generator.ui_tests --keepdb
cd ..
```

### Lint Job Replication

```bash
# 1. Create virtual environment
uv venv
source .venv/bin/activate

# 2. Install linting dependencies
uv pip install -r requirements.txt
uv pip install black ruff

# 3. Check code formatting
python -m black --check pillars/ tests/ webapp/ --exclude migrations

# 4. Run linting
python -m ruff check pillars/ tests/ webapp/ --exclude migrations
```

## Option 3: Using Docker Compose

Create a `docker-compose.test.yml` file to replicate the CI environment:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: pillars_test
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  test:
    build:
      context: .
      dockerfile: Dockerfile.test
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/pillars_test
      DJANGO_SECRET_KEY: test-secret-key-for-ci
      DJANGO_DEBUG: "True"
      DJANGO_ALLOWED_HOSTS: localhost,127.0.0.1
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - .:/app
    working_dir: /app
    command: >
      sh -c "
        uv venv &&
        source .venv/bin/activate &&
        uv pip install -r requirements.txt &&
        cd webapp &&
        python manage.py migrate &&
        python manage.py test --keepdb &&
        cd .. &&
        python -m pytest tests/ -v
      "
```

Then run:
```bash
docker-compose -f docker-compose.test.yml up --build
```

## Quick Test Script

You can also create a simple script to run the workflow steps:

```bash
#!/bin/bash
# test-ci.sh - Run CI workflow steps locally

set -e

export DATABASE_URL=${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/pillars_test}
export DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY:-test-secret-key-for-ci}
export DJANGO_DEBUG=True
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

echo "Setting up environment..."
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

echo "Running core library tests..."
python -m pytest tests/ -v

echo "Running Django webapp tests..."
cd webapp
python manage.py migrate
python manage.py collectstatic --noinput --clear
python manage.py test --keepdb
cd ..

echo "All tests passed!"
```

Make it executable:
```bash
chmod +x test-ci.sh
./test-ci.sh
```

## Troubleshooting

### `act` Issues

- **Docker not running:** Make sure Docker Desktop (or Docker daemon) is running
- **Permission errors:** On Linux, you may need to add your user to the docker group
- **Service containers not working:** Check that Docker networking is properly configured

### Manual Replication Issues

- **PostgreSQL connection errors:** Make sure PostgreSQL is running and accessible
- **Chrome/Chromium not found:** Install browser and chromedriver for E2E tests
- **Static files errors:** Run `collectstatic` before running Django tests

## Best Practices

1. **Test locally before pushing:** Always run tests locally to catch issues early
2. **Use the same Python version:** Match the Python version used in CI
3. **Keep dependencies in sync:** Ensure `requirements.txt` matches what's installed in CI
4. **Test E2E separately:** E2E tests are slower, so run them separately when needed
5. **Use `act` for quick checks:** Use `act` to verify workflow syntax and basic functionality

## Resources

- [act Documentation](https://github.com/nektos/act)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Documentation](https://docs.docker.com/)

