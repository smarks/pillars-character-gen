# Deployment Guide

## Quick Fix for CSRF Errors

If you're seeing "CSRF verification failed" errors on your server, follow these steps:

### 1. Update Your `.env` File

On your Linux server, edit your `.env` file and set:

```bash
# Your server's domain or IP
DJANGO_ALLOWED_HOSTS=your-server-ip,your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=http://your-server-ip,http://your-domain.com

# If NOT using HTTPS/SSL (most common for testing)
DJANGO_USE_HTTPS=False

# If you ARE using HTTPS/SSL
DJANGO_USE_HTTPS=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com
```

### 2. Restart Your Application

```bash
# If using systemd service
sudo systemctl restart pillars

# If running manually
pkill -f "python.*manage.py"
# Then restart your server
```

### 3. Test

Try submitting a form again. The CSRF error should be gone.

## Common CSRF Issues

### Issue: Forms fail with CSRF error
**Cause**: `CSRF_TRUSTED_ORIGINS` not set correctly
**Fix**: Add your server's URL to `DJANGO_CSRF_TRUSTED_ORIGINS` in `.env`

Example:
```bash
# For IP-based access
DJANGO_CSRF_TRUSTED_ORIGINS=http://192.168.1.100:8000

# For domain-based access
DJANGO_CSRF_TRUSTED_ORIGINS=http://pillars.example.com

# For HTTPS
DJANGO_CSRF_TRUSTED_ORIGINS=https://pillars.example.com

# Multiple origins (comma-separated)
DJANGO_CSRF_TRUSTED_ORIGINS=http://192.168.1.100:8000,http://pillars.local,https://pillars.example.com
```

### Issue: Cookies not being set
**Cause**: `DJANGO_USE_HTTPS=True` but server is HTTP
**Fix**: Set `DJANGO_USE_HTTPS=False` in `.env` if not using SSL

### Issue: "Allowed hosts" error
**Cause**: `ALLOWED_HOSTS` doesn't include your server's IP/domain
**Fix**: Add to `DJANGO_ALLOWED_HOSTS` in `.env`

```bash
DJANGO_ALLOWED_HOSTS=192.168.1.100,pillars.example.com,localhost
```

## Full Deployment Checklist

### 1. Environment Variables

Create `/path/to/pillars/.env`:

```bash
# Django Core
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-server-ip,your-domain.com
DJANGO_USE_HTTPS=False  # Set to True if using HTTPS
DJANGO_CSRF_TRUSTED_ORIGINS=http://your-server-ip,http://your-domain.com

# Default Users
PILLARS_ADMIN_USERNAME=admin
PILLARS_ADMIN_PASSWORD=secure-password-here
PILLARS_ADMIN_EMAIL=admin@example.com
PILLARS_DM_USERNAME=dm
PILLARS_DM_PASSWORD=another-secure-password
PILLARS_DM_EMAIL=dm@example.com
```

### 2. Generate Secret Key

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 3. Database Setup

```bash
cd webapp
python manage.py migrate
python manage.py create_default_users
```

### 4. Static Files (if using Nginx/Apache)

```bash
cd webapp
python manage.py collectstatic --noinput
```

### 5. Test Locally

```bash
# Set DEBUG=True temporarily to test
export DJANGO_DEBUG=True
python manage.py runserver 0.0.0.0:8000
```

Visit `http://your-server-ip:8000` and test forms.

### 6. Production Server

#### Option A: Gunicorn + Nginx

**Run Gunicorn**:
```bash
cd webapp
gunicorn webapp.wsgi:application --bind 127.0.0.1:8000
```

**Nginx Config** (`/etc/nginx/sites-available/pillars`):
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/pillars/webapp/staticfiles/;
    }
}
```

#### Option B: Systemd Service

Create `/etc/systemd/system/pillars.service`:

```ini
[Unit]
Description=Pillars Character Generator
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/pillars/webapp
Environment="PATH=/path/to/pillars/.venv/bin"
EnvironmentFile=/path/to/pillars/.env
ExecStart=/path/to/pillars/.venv/bin/gunicorn webapp.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable pillars
sudo systemctl start pillars
sudo systemctl status pillars
```

## HTTPS Setup (Recommended)

### Using Let's Encrypt (Free SSL)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

Then update `.env`:
```bash
DJANGO_USE_HTTPS=True
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com
```

## Troubleshooting

### Check Logs

```bash
# Django development server logs
# (printed to console)

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Systemd service logs
sudo journalctl -u pillars -f
```

### Test CSRF Cookie

Open browser DevTools → Application → Cookies

You should see:
- `csrftoken` cookie set
- Domain matches your server
- If HTTPS: `Secure` flag should be checked
- If HTTP: `Secure` flag should NOT be checked

### Verify Settings

```bash
cd webapp
python manage.py shell
```

```python
from django.conf import settings
print("DEBUG:", settings.DEBUG)
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
print("CSRF_TRUSTED_ORIGINS:", settings.CSRF_TRUSTED_ORIGINS)
print("CSRF_COOKIE_SECURE:", settings.CSRF_COOKIE_SECURE)
print("SESSION_COOKIE_SECURE:", settings.SESSION_COOKIE_SECURE)
```

## Security Notes

- Always use HTTPS in production (get free SSL from Let's Encrypt)
- Never commit `.env` file to git (it's in `.gitignore`)
- Use strong passwords for admin/DM accounts
- Keep `SECRET_KEY` secret and unique per deployment
- Set `DEBUG=False` in production
- Regularly update Django: `pip install --upgrade django`

## Support

For issues:
1. Check this deployment guide
2. Check Django logs
3. Verify all environment variables are set
4. Test with `DEBUG=True` (temporarily) to see detailed errors
5. File an issue at https://github.com/smarks/pillars-character-gen/issues
