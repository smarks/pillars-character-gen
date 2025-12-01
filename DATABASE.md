# Database Configuration

This project uses PostgreSQL for both production and testing environments.

## Database Overview

| Environment | Database Name | Purpose |
|-------------|---------------|---------|
| Production | `pillars_db` | Live application data |
| Test | `pillars_db_test` | Testing and development |

## Connection Details

Both databases run on the same PostgreSQL server:

- **Host:** localhost (or your server IP for remote connections)
- **Port:** 5432
- **Username:** pillars
- **Password:** pillars

### Connection URLs

```
# Production
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db

# Test
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test
```

## Local Development Setup

### Option 1: Use the Test Database (Recommended)

Copy `.env.test` to your local `.env` file:

```bash
cp .env.test .env
```

This configures your local environment to use the test database with debug mode enabled.

### Option 2: Set DATABASE_URL Directly

Override the database URL when running commands:

```bash
# Run development server
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test python manage.py runserver

# Run migrations
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test python manage.py migrate

# Run tests
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test python manage.py test
```

### Option 3: Export the Variable

Set the environment variable for your terminal session:

```bash
export DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test

# Now all commands use the test database
python manage.py runserver
python manage.py migrate
python manage.py test
```

## Remote Development

If connecting to the server remotely, replace `localhost` with the server IP:

```
DATABASE_URL=postgres://pillars:pillars@<SERVER_IP>:5432/pillars_db_test
```

Ensure PostgreSQL is configured to accept remote connections (check `pg_hba.conf` and `postgresql.conf`).

## Running Migrations

Always run migrations on the test database during development:

```bash
cd webapp
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test python manage.py migrate
```

## Creating Test Data

To set up default users on the test database:

```bash
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db_test python manage.py create_default_users
```

## Important Notes

- **Never use `pillars_db` for testing** - this is the production database
- The server's `.env` file points to production; do not modify it
- Use `.env.test` or set `DATABASE_URL` explicitly for all development work
- Both databases share the same schema and migrations
