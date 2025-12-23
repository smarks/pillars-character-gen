# Pillars Character Generator

A Django web application for creating and managing characters for the Pillars tabletop RPG.

## Quick Start

```bash
cd webapp
source ../.venv/bin/activate
python manage.py runserver
```

Open http://127.0.0.1:8000 in your browser.

## Setup From Scratch

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

## Running Tests

```bash
cd webapp
python manage.py test
```

## Configuration

The app uses SQLite by default. See `.env.example` for all configuration options including:
- PostgreSQL database setup
- Production deployment settings (gunicorn, HTTPS)
- Default user credentials

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
└── requirements.txt
```
