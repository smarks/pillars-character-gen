
# Authentication System Documentation

## Overview

The Pillars RPG Character Generator uses Django's built-in authentication system with a custom role-based access control layer. The system supports three user roles (Player, DM, Admin) with hierarchical permissions for managing characters and accessing restricted content.

## Architecture

### Core Components

- **Framework**: Django 5.1.3 built-in auth (`django.contrib.auth`)
- **User Model**: Standard Django User model (username/password)
- **Extended Profile**: Custom `UserProfile` model with role management
- **Session Management**: Session-based authentication (no tokens)
- **Database**: SQLite (`webapp/db.sqlite3`)

### Data Models

#### Django User Model (Built-in)
```python
username      # Required, unique identifier
password      # Hashed (PBKDF2 by default)
email         # Optional
is_staff      # Django admin access flag
is_superuser  # Django superuser flag
is_active     # Account enabled/disabled
```

#### UserProfile Model
**Location**: `webapp/webapp/generator/models.py:22-45`

```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    roles = models.JSONField(default=list)  # ['player'], ['dm'], ['admin'], or combinations
    phone = models.CharField(max_length=20, blank=True, default='')
    discord_handle = models.CharField(max_length=100, blank=True, default='')
```

**Access Pattern**: `request.user.profile.is_dm`

## Role System

### Role Definitions

| Role | Identifier | Permissions |
|------|-----------|-------------|
| **Player** | `'player'` | Create/save characters, view public content |
| **Dungeon Master** | `'dm'` | Player permissions + DM Handbook access |
| **Admin** | `'admin'` | DM permissions + User management |

### Multi-Role Support

Users can hold multiple roles simultaneously. The system stores roles as a JSON list:

```python
# Examples
['player']              # Basic player
['dm']                  # DM only
['admin', 'dm']         # Admin with DM access
['player', 'dm']        # Player who is also a DM
```

### Role Properties (UserProfile)

```python
@property
def is_player(self):
    return 'player' in self.roles

@property
def is_dm(self):
    return 'dm' in self.roles

@property
def is_admin(self):
    return 'admin' in self.roles

def has_role(self, role):
    return role in self.roles

def get_roles_display(self):
    # Returns "Player, Dungeon Master, Admin" etc.
```

## Authentication Views

### Registration
**URL**: `/register/`
**Template**: `generator/register.html`
**Location**: `views.py:1218-1233`

**Form Fields**:
- Username (required)
- Password / Confirm Password (required)
- Role (dropdown: Player or DM only)
- Email (optional)
- Phone (optional - for future SMS notifications)
- Discord Handle (optional - format: username#1234)

**Process**:
1. User submits registration form
2. Form validates username uniqueness and password match
3. Creates User record with hashed password
4. Creates UserProfile with selected role
5. Auto-login (sets session cookie)
6. Redirects to welcome page

**Security Notes**:
- Admin role cannot be selected during registration
- Admin role must be assigned via Manage Users page
- Already-authenticated users are redirected to welcome page

### Login
**URL**: `/login/`
**Template**: `generator/login.html`
**Location**: `views.py:1236-1251`

**Features**:
- Standard Django `AuthenticationForm`
- Supports `?next=` parameter for post-login redirects
- Shows error messages for invalid credentials
- Redirects authenticated users to welcome page

**Process**:
1. User submits username/password
2. Django's `authenticate()` checks credentials (password hash comparison)
3. On success: `login()` creates session, redirects to `next` or welcome
4. On failure: Shows error message, re-renders form

### Logout
**URL**: `/logout/`
**Location**: `views.py:1254-1258`

**Process**:
1. Calls Django's `logout()` to clear session
2. Shows info message: "You have been logged out"
3. Redirects to welcome page

## Authorization System

### Built-in Decorator: `@login_required`

Used on views requiring any authenticated user:

```python
@login_required
def save_character(request):
    # Only logged-in users can save characters
```

**Protected Views**:
- `save_character` (views.py:1265)
- `my_characters` (views.py:1301)
- `load_character` (views.py:1308)
- `delete_character` (views.py:1336)

**Behavior**: Redirects to `/login/?next=<current-url>` if not authenticated

### Custom Decorator: `@dm_required`
**Location**: `views.py:1355-1364`

```python
def dm_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not (request.user.profile.is_dm or request.user.profile.is_admin):
            messages.error(request, 'You must be a Dungeon Master to access this page.')
            return redirect('welcome')
        return view_func(request, *args, **kwargs)
    return wrapper
```

**Protected Views**:
- `dm_handbook` (views.py:1379)

**Behavior**:
- Requires authentication AND (DM role OR Admin role)
- Shows error message if unauthorized
- Redirects to welcome page

### Custom Decorator: `@admin_required`
**Location**: `views.py:1367-1376`

```python
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'profile') or not request.user.profile.is_admin:
            messages.error(request, 'You must be an Admin to access this page.')
            return redirect('welcome')
        return view_func(request, *args, **kwargs)
    return wrapper
```

**Protected Views**:
- `manage_users` (views.py:1385)
- `change_user_role` (views.py:1393)

**Behavior**:
- Requires authentication AND Admin role
- Shows error message if unauthorized
- Redirects to welcome or login

## Character Ownership System

### SavedCharacter Model
**Location**: `models.py:47-59`

```python
class SavedCharacter(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_characters')
    name = models.CharField(max_length=200)
    character_data = models.JSONField()  # Full character state
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Ownership Model**:
- Characters belong to users via `ForeignKey`
- Cascade delete: If user deleted, their characters are deleted
- Access controlled via query filtering

### Save Character
**URL**: `/save-character/` (POST only)
**Decorator**: `@login_required`, `@require_POST`
**Location**: `views.py:1265-1298`

**Process**:
1. Reads `current_character` from session
2. Gets character name from POST data or generates default
3. Includes all interactive experience data from session keys
4. Creates `SavedCharacter` with `user=request.user` (ownership)
5. Returns JSON: `{success: true, id: <id>, name: <name>}`

**Security**: Only logged-in users can save, ownership automatically assigned

### Load Character
**URL**: `/load-character/<int:char_id>/`
**Decorator**: `@login_required`
**Location**: `views.py:1308-1333`

**Process**:
1. Query: `SavedCharacter.objects.filter(id=char_id, user=request.user)`
2. Validates user owns the character (returns 404 if not)
3. Restores character data to session keys
4. Restores experience data to interactive session keys
5. Redirects to generator page

**Security**: Ownership enforced via database query filter

### Delete Character
**URL**: `/delete-character/<int:char_id>/`
**Decorator**: `@login_required`, `@require_POST`
**Location**: `views.py:1336-1348`

**Process**:
1. Query: `SavedCharacter.objects.filter(id=char_id, user=request.user)`
2. Validates ownership (returns 404 if not owner)
3. Deletes record
4. Shows success message
5. Redirects to My Characters page

**Security**: Ownership enforced + POST-only (prevents CSRF)

## User Management (Admin Only)

### Manage Users Page
**URL**: `/manage-users/`
**Decorator**: `@admin_required`
**Template**: `generator/manage_users.html`
**Location**: `views.py:1385-1390`

**Features**:
- Lists all UserProfile records with user data
- Shows username, email, current roles
- Provides checkboxes for role assignment (player, dm, admin)
- Each user has a "Save" button to update roles

**UI Example**:
```
Username    Email              Roles
--------    -----              -----
sam         sam@example.com    ☑ Player  ☑ DM  ☑ Admin   [Save]
alice       alice@ex.com       ☑ Player  ☐ DM  ☐ Admin   [Save]
bob         bob@example.com    ☐ Player  ☑ DM  ☐ Admin   [Save]
```

### Change User Role
**URL**: `/change-role/<int:user_id>/`
**Decorator**: `@admin_required`, `@require_POST`
**Location**: `views.py:1393-1409`

**Process**:
1. Gets UserProfile by user_id
2. Reads role checkboxes from POST data
3. Validates roles against `ROLE_CHOICES` whitelist
4. Updates `profile.roles` (JSON list)
5. Saves profile
6. Shows success message with new roles
7. Redirects to Manage Users page

**Security**: Admin-only, POST-only, validates role choices

## Default User Creation

### Management Command
**Command**: `python manage.py create_default_users`
**Location**: `webapp/webapp/generator/management/commands/create_default_users.py`

**Environment Variables**:
```bash
# Admin user (gets roles: ['admin', 'dm'])
PILLARS_ADMIN_USERNAME=sam        # default, can override
PILLARS_ADMIN_PASSWORD=required   # MUST be set
PILLARS_ADMIN_EMAIL=optional

# DM user (gets roles: ['dm'])
PILLARS_DM_USERNAME=dm            # default, can override
PILLARS_DM_PASSWORD=required      # MUST be set
PILLARS_DM_EMAIL=optional
```

**Example Usage**:
```bash
# Set passwords in environment
export PILLARS_ADMIN_PASSWORD="secure_admin_pass_123"
export PILLARS_DM_PASSWORD="secure_dm_pass_456"

# Run command
python manage.py create_default_users

# Or inline
PILLARS_ADMIN_PASSWORD=test123 PILLARS_DM_PASSWORD=test456 python manage.py create_default_users
```

**Behavior**:
- Creates or updates users (idempotent)
- Admin gets `['admin', 'dm']` roles
- DM gets `['dm']` role only
- Uses Django's `set_password()` for secure hashing
- Skips creation if password env var not set (shows warning)

**Production Use**: Typically run during deployment to bootstrap admin/DM accounts

## Settings Configuration

### Location: `webapp/webapp/settings.py`

### Authentication Settings (Lines 144-147)
```python
LOGIN_URL = 'login'                # Where @login_required redirects
LOGIN_REDIRECT_URL = 'welcome'     # Where login() redirects after success
LOGOUT_REDIRECT_URL = 'welcome'    # Where logout() redirects
```

### Password Validation (Lines 110-118)
```python
if DEBUG:
    # Development: No password requirements
    AUTH_PASSWORD_VALIDATORS = []
else:
    # Production: Full validation
    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    ]
```

**Development**: No password restrictions (easy testing)
**Production**: Enforces strong passwords (length, complexity, not common)

### Security Settings (Lines 149-156)
```python
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True          # Enable XSS filter
    SECURE_CONTENT_TYPE_NOSNIFF = True        # Prevent MIME sniffing
    X_FRAME_OPTIONS = "DENY"                  # Prevent clickjacking
    CSRF_COOKIE_SECURE = True                 # CSRF cookie HTTPS-only
    SESSION_COOKIE_SECURE = True              # Session cookie HTTPS-only
```

**Production-Only**: Requires HTTPS for secure cookies

### Middleware (Lines 66-74)
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",            # CSRF protection
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Sets request.user
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

**AuthenticationMiddleware**: Adds `request.user` to all views

## UI Components

### User Bar (All Pages)
**Template**: `generator/base.html:238-247`

```django
<div class="user-bar no-print">
    {% if user.is_authenticated %}
        <span class="username">{{ user.username }}</span>
        <a href="{% url 'my_characters' %}">My Characters</a>
        <a href="{% url 'logout' %}">Logout</a>
    {% else %}
        <a href="{% url 'login' %}">Login</a>
        <a href="{% url 'register' %}">Register</a>
    {% endif %}
</div>
```

**Location**: Upper-right corner of every page
**Behavior**: Shows username and links based on auth status

### Role-Based Visibility (Welcome Page)

**DM Handbook Link** (DM or Admin only):
```django
{% if user.is_authenticated and user.profile.is_dm or user.is_authenticated and user.profile.is_admin %}
    <a href="{% url 'dm' %}" class="nav-link">DM Handbook</a>
{% endif %}
```

**Manage Users Link** (Admin only):
```django
{% if user.is_authenticated and user.profile.is_admin %}
    <a href="{% url 'manage_users' %}" class="nav-link">Manage Users</a>
{% endif %}
```

## Security Features

### 1. Password Security
- **Hashing**: Django's default PBKDF2 algorithm
- **Validation**: Enforced in production (length, complexity, common passwords)
- **Storage**: Stored as hash in database (format: `pbkdf2_sha256$<iterations>$<salt>$<hash>`)

### 2. CSRF Protection
- **Token Required**: All POST requests require `{% csrf_token %}` in forms
- **Middleware**: `CsrfViewMiddleware` validates tokens
- **Cookies**: CSRF cookies secured in production (HTTPS-only)

### 3. Session Security
- **Session-Based Auth**: No tokens exposed in URLs or localStorage
- **Secure Cookies**: HTTPS-only in production
- **Logout Clears Session**: Complete session destruction on logout

### 4. Authorization Checks
- **Ownership Validation**: Character load/delete filtered by `user=request.user`
- **Role Decorators**: `@dm_required`, `@admin_required` enforce permissions
- **Template Guards**: UI elements hidden based on roles

### 5. Input Validation
- **Django Forms**: All user input validated via forms
- **Role Whitelist**: Role changes validated against `ROLE_CHOICES`
- **POST-Only**: Destructive actions require POST (prevents CSRF)

### 6. Database Query Security
- **ORM Usage**: No raw SQL (prevents SQL injection)
- **Parameterized Queries**: Django ORM handles escaping
- **Ownership Filters**: All character queries filter by user

## Testing

### Test Suite
**Location**: `webapp/webapp/generator/tests.py:529-636`

**Role Tests**:
```python
test_user_creation_with_different_roles()        # Verify role assignment
test_user_profile_role_properties()              # Test is_player, is_dm, is_admin
test_multi_role_user()                           # Test users with multiple roles
test_player_cannot_access_manage_users()         # 403 for players
test_dm_cannot_access_manage_users()             # DM can't access admin pages
test_admin_can_access_manage_users()             # Admin has access
test_player_cannot_see_dm_links()                # UI visibility checks
test_dm_can_see_dm_handbook_link()               # DM sees DM content
test_unauthenticated_cannot_access_manage_users() # Redirect to login
```

**Test Coverage**: Role-based access control, UI visibility, ownership validation

**Run Tests**:
```bash
cd webapp
python manage.py test generator.tests.UserRoleTests -v 2
```

## Authentication Flow Diagrams

### Registration Flow
```
User → /register/
  ↓
Fill form (username, password, role, optional email/phone/discord)
  ↓
Submit → RegistrationForm validation
  ↓
Create User (password hashed)
  ↓
Create UserProfile (with selected role)
  ↓
Auto-login (set session)
  ↓
Redirect → /welcome/
```

### Login Flow
```
User → /login/ (or redirected by @login_required)
  ↓
Enter username/password
  ↓
Submit → authenticate() checks password hash
  ↓
Success → login() sets session → Redirect to ?next or /welcome/
  ↓
Failure → Show error → Re-render form
```

### Authorization Check (DM Handbook Example)
```
User → /dm/
  ↓
@dm_required decorator
  ↓
Is authenticated? → No → Redirect to /login/?next=/dm/
  ↓ Yes
Has profile? → No → Redirect to /welcome/ with error
  ↓ Yes
Is DM or Admin? → No → Redirect to /welcome/ with error
  ↓ Yes
Render DM Handbook
```

### Character Save Flow
```
User creates character in generator (session storage)
  ↓
Click "Save" → POST /save-character/
  ↓
@login_required check → Redirect to login if not authenticated
  ↓
Read current_character from session
  ↓
Read interactive_* data from session
  ↓
Create SavedCharacter(user=request.user, name=..., character_data=...)
  ↓
Save to database
  ↓
Return JSON {success: true, id: X, name: Y}
  ↓
Frontend shows confirmation
```

### Character Load Flow
```
User → My Characters page
  ↓
Click "Load" on character → GET /load-character/123/
  ↓
@login_required check
  ↓
Query: SavedCharacter.objects.filter(id=123, user=request.user)
  ↓
Found? → No → 404 error
  ↓ Yes
Restore character_data to session['current_character']
  ↓
Restore experience data to session['interactive_*']
  ↓
Redirect → /generator/
```

## URL Routes

### Authentication Routes
```python
path('login/', views.login_view, name='login'),
path('logout/', views.logout_view, name='logout'),
path('register/', views.register_view, name='register'),
```

### Character Management (Login Required)
```python
path('my-characters/', views.my_characters, name='my_characters'),
path('save-character/', views.save_character, name='save_character'),
path('load-character/<int:char_id>/', views.load_character, name='load_character'),
path('delete-character/<int:char_id>/', views.delete_character, name='delete_character'),
```

### DM Routes (DM or Admin Required)
```python
path('dm/', views.dm_handbook, name='dm'),
```

### Admin Routes (Admin Only)
```python
path('manage-users/', views.manage_users, name='manage_users'),
path('change-role/<int:user_id>/', views.change_user_role, name='change_user_role'),
```

## Known Limitations

### 1. No Password Reset
- Password reset functionality not implemented
- Would require email server configuration (SMTP)
- Users who forget passwords need admin intervention

### 2. No Email Verification
- Email addresses accepted but not verified
- Could lead to invalid emails in database

### 3. No Rate Limiting
- Login endpoint not rate-limited
- Vulnerable to brute-force attacks in production
- Consider adding django-axes or similar

### 4. No Two-Factor Authentication
- Single-factor (password-only) authentication
- Higher-risk for admin accounts

### 5. No API Authentication
- No JWT, OAuth, or token-based auth
- Only session-based web interface
- Cannot be used as API backend

### 6. Session Persistence
- Users can be logged in from multiple devices
- No "force logout other sessions" feature

### 7. No Account Deletion
- No self-service account deletion
- Would need to be done via Django admin or database

## Production Deployment Checklist

### Environment Configuration
- [ ] Set strong `DJANGO_SECRET_KEY` (50+ random characters)
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure `DJANGO_ALLOWED_HOSTS` (your domain)
- [ ] Configure `DJANGO_CSRF_TRUSTED_ORIGINS` (https://yourdomain.com)
- [ ] Set strong `PILLARS_ADMIN_PASSWORD` and `PILLARS_DM_PASSWORD`

### Database & Users
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create default users: `python manage.py create_default_users`
- [ ] Test admin login

### Security
- [ ] Enable HTTPS (required for secure cookies)
- [ ] Verify password validators enabled (auto-enabled when DEBUG=False)
- [ ] Verify secure cookies enabled (auto-enabled when DEBUG=False)
- [ ] Consider adding rate limiting (django-axes)
- [ ] Consider adding 2FA for admin accounts (django-otp)
- [ ] Review CORS settings if adding API

### Testing
- [ ] Test login/logout
- [ ] Test registration (player and DM roles)
- [ ] Test role-based access (try accessing /dm/ as player)
- [ ] Test character save/load/delete
- [ ] Test admin user management
- [ ] Verify unauthorized access redirects work

### Monitoring
- [ ] Set up error logging (configure LOGGING in settings.py)
- [ ] Monitor failed login attempts
- [ ] Set up backup system for db.sqlite3

## Development vs Production

| Feature | Development (DEBUG=True) | Production (DEBUG=False) |
|---------|-------------------------|--------------------------|
| Password Validation | Disabled | Enabled (4 validators) |
| CSRF Cookie Security | HTTP allowed | HTTPS required |
| Session Cookie Security | HTTP allowed | HTTPS required |
| XSS Filter | Disabled | Enabled |
| Error Pages | Detailed traceback | Generic 500 page |
| Static Files | Served by runserver | Requires collectstatic |

## Common Tasks

### Create a New Admin User
```bash
export PILLARS_ADMIN_USERNAME=newadmin
export PILLARS_ADMIN_PASSWORD=securepass123
export PILLARS_ADMIN_EMAIL=admin@example.com
python manage.py create_default_users
```

### Promote User to Admin (via Django shell)
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='alice')
user.profile.roles = ['admin', 'dm']
user.profile.save()
```

### Reset a User's Password (via Django shell)
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='bob')
user.set_password('newpassword123')
user.save()
```

### List All Users and Roles (via Django shell)
```bash
python manage.py shell
```
```python
from webapp.generator.models import UserProfile
for profile in UserProfile.objects.all():
    print(f"{profile.user.username}: {profile.get_roles_display()}")
```

## File Reference

| File Path | Purpose |
|-----------|---------|
| `webapp/webapp/settings.py` | Auth config, password validators, security settings |
| `webapp/webapp/generator/models.py` | UserProfile, SavedCharacter models |
| `webapp/webapp/generator/views.py` | Auth views, decorators, character save/load |
| `webapp/webapp/generator/urls.py` | URL routing |
| `webapp/webapp/generator/forms.py` | RegistrationForm |
| `webapp/webapp/generator/templates/generator/base.html` | User bar component |
| `webapp/webapp/generator/templates/generator/login.html` | Login form |
| `webapp/webapp/generator/templates/generator/register.html` | Registration form |
| `webapp/webapp/generator/templates/generator/manage_users.html` | Admin user management |
| `webapp/webapp/generator/templates/generator/my_characters.html` | User's saved characters |
| `webapp/webapp/generator/management/commands/create_default_users.py` | Default user creation CLI |
| `webapp/webapp/generator/tests.py` | Role and permission tests |
| `.env.example` | Environment variable examples |

## Support & Troubleshooting

### User Can't Log In
1. Verify account exists in database
2. Check password (may need reset via shell)
3. Verify `is_active=True` on User model
4. Check browser console for CSRF errors

### Can't Access Admin Pages
1. Verify user has 'admin' role (not just is_staff)
2. Check UserProfile.roles field in database
3. Verify middleware is enabled in settings.py

### Characters Not Saving
1. Verify user is logged in
2. Check session is active (try logout/login)
3. Verify SavedCharacter table exists (run migrations)
4. Check browser console for JavaScript errors

### CSRF Token Missing
1. Verify `{% csrf_token %}` in all POST forms
2. Check `CsrfViewMiddleware` in MIDDLEWARE
3. Verify cookies enabled in browser
4. Check CSRF_TRUSTED_ORIGINS for domain

---

**Last Updated**: 2025-12-01
**Django Version**: 5.1.3
**Python Version**: 3.11+