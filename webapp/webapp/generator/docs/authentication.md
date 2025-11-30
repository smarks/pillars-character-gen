# Authentication System

The Pillars Character Generator uses **Django's built-in authentication** with custom extensions.

## Overview

- **Framework**: Django's `django.contrib.auth`
- **Database**: SQLite (`db.sqlite3`)
- **Session-based**: Uses Django sessions for login state
- **Password validation**: Disabled in development (`AUTH_PASSWORD_VALIDATORS = []`)

## Models

### UserProfile (`models.py:5-19`)

One-to-one extension of Django's `User` model:

- `role`: User role - either `'player'` or `'dm'` (Dungeon Master). Defaults to `'player'`
- `phone`: Optional phone number for SMS notifications
- `discord_handle`: Optional Discord username
- Created automatically during registration

#### Roles

| Role | Value | Description |
|------|-------|-------------|
| Player | `'player'` | Standard user who creates and plays characters |
| Dungeon Master | `'dm'` | Game master with potential access to DM-specific features |

Access the role via `request.user.profile.role` in views or `user.profile.role` in templates.

### SavedCharacter (`models.py:15-27`)

Links characters to users:

- `user`: ForeignKey to User
- `name`: Character name
- `character_data`: JSON field storing full character state
- `created_at` / `updated_at`: Timestamps

## URL Routes

| URL | View | Purpose |
|-----|------|---------|
| `/login/` | `login_view` | User login |
| `/logout/` | `logout_view` | User logout |
| `/register/` | `register_view` | New account creation |
| `/my-characters/` | `my_characters` | List saved characters |
| `/save-character/` | `save_character` | Save current character (POST, AJAX) |
| `/load-character/<id>/` | `load_character` | Load saved character into session |
| `/delete-character/<id>/` | `delete_character` | Delete a saved character (POST) |
| `/manage-users/` | `manage_users` | DM-only: List and manage user roles |
| `/change-role/<id>/` | `change_user_role` | DM-only: Change a user's role (POST) |

## Views

### Registration (`views.py:1190-1205`)

- Uses custom `RegistrationForm` extending `UserCreationForm`
- Collects: username, password, role selection, optional email/phone/Discord
- Auto-creates `UserProfile` with selected role on save
- Auto-logs in user after registration

### Login (`views.py:1208-1223`)

- Uses Django's `AuthenticationForm`
- Supports `?next=` redirect parameter
- Redirects authenticated users to welcome page

### Logout (`views.py:1226-1230`)

- Clears session and redirects to welcome

## Protected Views

Uses `@login_required` decorator:

- `save_character` - Save current character (also uses `@require_POST`)
- `my_characters` - View saved characters list
- `load_character` - Load a character into session
- `delete_character` - Delete a character (also uses `@require_POST`)

### DM-Only Views

Uses `@dm_required` decorator (requires `role == 'dm'`):

- `manage_users` - View all users and their roles
- `change_user_role` - Change any user's role (also uses `@require_POST`)

## Character Save/Load Flow

### Save

POST to `/save-character/` with optional `name` parameter:

1. Reads `current_character` from session
2. Includes interactive experience data (`interactive_years`, `interactive_skills`, etc.)
3. Creates new `SavedCharacter` record
4. Returns JSON: `{ success: true, id: <id>, name: <name> }`

### Load

GET `/load-character/<id>/`:

1. Validates user owns the character
2. Restores character data to session
3. Restores experience data to session
4. Redirects to generator with success message

## Settings

```python
# settings.py
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'welcome'
LOGOUT_REDIRECT_URL = 'welcome'
```

## Security Notes

- CSRF protection enabled on all forms
- Character ownership validated on load/delete
- Character deletion requires client-side confirmation

### Development Mode Warnings

- Password validation disabled (`AUTH_PASSWORD_VALIDATORS = []`)
- `DEBUG = True`
- Insecure secret key in use

For production, update `settings.py` with:
- Strong `SECRET_KEY`
- `DEBUG = False`
- Password validators enabled
- HTTPS configuration

## Default Accounts

A default DM account is created for administration:

| Username | Password | Role |
|----------|----------|------|
| `dm` | `foobar` | Dungeon Master |

**Change the password in production!**
