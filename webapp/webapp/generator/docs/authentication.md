# Authentication System

The Pillars Character Generator uses **Django's built-in authentication** with custom extensions.

## Overview

- **Framework**: Django's `django.contrib.auth`
- **Database**: SQLite (`db.sqlite3`)
- **Session-based**: Uses Django sessions for login state
- **Password validation**: Disabled in development (`AUTH_PASSWORD_VALIDATORS = []`)

## Models

### UserProfile (`models.py:5-41`)

One-to-one extension of Django's `User` model:

- `roles`: JSON list of role strings. Users can have multiple roles.
- `phone`: Optional phone number for SMS notifications
- `discord_handle`: Optional Discord username
- Created automatically during registration

#### Roles

| Role | Value | Description |
|------|-------|-------------|
| Player | `'player'` | Standard user who creates and plays characters |
| Dungeon Master | `'dm'` | Game master with access to DM handbook |
| Admin | `'admin'` | Full access including user management |

Users can have multiple roles (e.g., `['admin', 'dm']`).

#### Helper Methods

```python
profile.has_role('dm')      # Check for specific role
profile.is_admin()          # Check if admin
profile.is_dm()             # Check if DM
profile.is_player()         # Check if player
profile.get_roles_display() # Human-readable role list
```

Access in templates:
```django
{% if user.profile.is_admin %}...{% endif %}
{% if user.profile.is_dm %}...{% endif %}
```

### SavedCharacter (`models.py:44-56`)

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
| `/manage-users/` | `manage_users` | Admin-only: List and manage user roles |
| `/change-role/<id>/` | `change_user_role` | Admin-only: Change a user's roles (POST) |

## Views

### Registration

- Uses custom `RegistrationForm` extending `UserCreationForm`
- Collects: username, password, role selection (player or DM), optional email/phone/Discord
- Admin role can only be assigned via the Manage Users page
- Auto-creates `UserProfile` with selected role on save
- Auto-logs in user after registration

### Login

- Uses Django's `AuthenticationForm`
- Supports `?next=` redirect parameter
- Redirects authenticated users to welcome page

### Logout

- Clears session and redirects to welcome

## Protected Views

Uses `@login_required` decorator:

- `save_character` - Save current character (also uses `@require_POST`)
- `my_characters` - View saved characters list
- `load_character` - Load a character into session
- `delete_character` - Delete a character (also uses `@require_POST`)

### DM-Only Views

Uses `@dm_required` decorator (requires DM or Admin role):

- DM Handbook page

### Admin-Only Views

Uses `@admin_required` decorator (requires Admin role):

- `manage_users` - View all users and their roles
- `change_user_role` - Change any user's roles (also uses `@require_POST`)

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
- Admin role cannot be self-assigned during registration

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

### Development

For local development, create users manually via Django shell or admin.

### Deployment

Use the management command with environment variables:

```bash
# Set environment variables
export PILLARS_ADMIN_USERNAME=sam        # optional, defaults to 'sam'
export PILLARS_ADMIN_PASSWORD=secretpass # required
export PILLARS_ADMIN_EMAIL=sam@example.com # optional

export PILLARS_DM_USERNAME=dm            # optional, defaults to 'dm'
export PILLARS_DM_PASSWORD=secretpass    # required
export PILLARS_DM_EMAIL=dm@example.com   # optional

# Run the command
python manage.py create_default_users
```

Add this to your deployment script after `migrate`:

```bash
python manage.py migrate
python manage.py create_default_users
```

| User | Environment Variables | Default Roles |
|------|----------------------|---------------|
| Admin | `PILLARS_ADMIN_*` | admin, dm |
| DM | `PILLARS_DM_*` | dm |

If a password variable is not set, that user will be skipped.
