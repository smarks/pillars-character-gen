# Pillars Character Generator - Deployment Guide

Complete guide to deploy the Pillars RPG Character Generator on a Linux server with HTTPS.

## Prerequisites

- Ubuntu/Debian Linux server
- Python 3.10+
- Git
- sudo access

## 1. Clone the Repository

```bash
cd /home/your-username/dev
git clone https://github.com/smarks/pillars-character-gen.git
cd pillars-character-gen
```

## 2. Set Up Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure Environment Variables

```bash
cp .env.example .env
nano .env
```

Update these values in `.env`:

```bash
# Generate a secret key
DJANGO_SECRET_KEY='your-secret-key-here'

# Your domain and/or IP addresses
DJANGO_ALLOWED_HOSTS=yourdomain.com,your-server-ip
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Set to True if using HTTPS (recommended)
DJANGO_USE_HTTPS=True

# Set to False for production
DJANGO_DEBUG=False

# Admin credentials
PILLARS_ADMIN_USERNAME=admin
PILLARS_ADMIN_PASSWORD=your-secure-password
PILLARS_ADMIN_EMAIL=admin@example.com

# DM credentials
PILLARS_DM_USERNAME=dm
PILLARS_DM_PASSWORD=another-secure-password
PILLARS_DM_EMAIL=dm@example.com
```

Generate a secret key:

```bash
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

## 4. Database Setup

### Option A: SQLite (Simple, default)

No configuration needed - works out of the box.

### Option B: PostgreSQL (Recommended for production)

Install PostgreSQL:

```bash
sudo apt install postgresql postgresql-contrib
```

Create database and user:

```bash
sudo -u postgres psql -c "CREATE USER pillars WITH PASSWORD 'pillars';"
sudo -u postgres psql -c "CREATE DATABASE pillars_db OWNER pillars;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE pillars_db TO pillars;"
```

Add to `.env`:

```bash
DATABASE_URL=postgres://pillars:pillars@localhost:5432/pillars_db
```

## 5. Initialize the Application

```bash
source .venv/bin/activate
cd webapp
python manage.py migrate
python manage.py create_default_users
python manage.py collectstatic --noinput
```

## 6. Create Systemd Service

Create the service file:

```bash
sudo nano /etc/systemd/system/pillars.service
```

Add this content (adjust paths as needed):

```ini
[Unit]
Description=Pillars Character Generator
After=network.target

[Service]
Type=simple
User=your-username
Group=your-username
WorkingDirectory=/home/your-username/dev/pillars-character-gen/webapp
EnvironmentFile=/home/your-username/dev/pillars-character-gen/.env
ExecStart=/home/your-username/dev/pillars-character-gen/.venv/bin/gunicorn \
    --workers 3 \
    --bind 0.0.0.0:9066 \
    --access-logfile - \
    --error-logfile - \
    webapp.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pillars
sudo systemctl start pillars
sudo systemctl status pillars
```

## 7. Set Up Nginx Reverse Proxy

Install nginx:

```bash
sudo apt install nginx
```

Create the site config:

```bash
sudo nano /etc/nginx/sites-available/pillars
```

Add this content:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:9066;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/your-username/dev/pillars-character-gen/webapp/staticfiles/;
    }
}
```

Enable the site:

```bash
sudo ln -sf /etc/nginx/sites-available/pillars /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Set Up HTTPS with Let's Encrypt (Free SSL)

### Get a Domain Name

If you don't have a domain, get a free one from DuckDNS:

1. Go to https://www.duckdns.org and sign in
2. Create a subdomain (e.g., `yourapp.duckdns.org`)
3. Point it to your server's public IP

Set up auto-updating (for dynamic IPs):

```bash
mkdir -p ~/duckdns
nano ~/duckdns/duck.sh
```

Add (replace with your values):

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOURSUBDOMAIN&token=YOUR-TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

Make executable and test:

```bash
chmod +x ~/duckdns/duck.sh
~/duckdns/duck.sh
cat ~/duckdns/duck.log  # Should show "OK"
```

Add to crontab for auto-updates:

```bash
crontab -e
```

Add this line:

```
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

### Port Forwarding

If your server is behind a router, forward these ports to your server:
- Port 80 (HTTP) → server-ip:80
- Port 443 (HTTPS) → server-ip:443

### Install SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Certbot will:
- Obtain a free SSL certificate
- Automatically configure nginx for HTTPS
- Set up auto-renewal

### Update Django Settings

Edit `.env` to add your domain:

```bash
DJANGO_ALLOWED_HOSTS=yourdomain.com,your-server-ip
DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com
DJANGO_USE_HTTPS=True
```

Restart the service:

```bash
sudo systemctl restart pillars
```

## 9. Verify Deployment

Visit https://yourdomain.com in your browser. You should see the Pillars Character Generator.

Test login with the credentials you set in `.env`.

## Updating the Application

After pulling new code:

```bash
cd /home/your-username/dev/pillars-character-gen
git pull
./deploy.sh
```

Or for a quick restart without migrations:

```bash
./deploy.sh quick
```

## Troubleshooting

### Check service logs

```bash
sudo journalctl -u pillars -f
```

### Check nginx logs

```bash
sudo tail -f /var/log/nginx/error.log
```

### Test nginx config

```bash
sudo nginx -t
```

### Verify Django settings

```bash
cd webapp
source ../.venv/bin/activate
python manage.py shell
```

```python
from django.conf import settings
print("ALLOWED_HOSTS:", settings.ALLOWED_HOSTS)
print("CSRF_TRUSTED_ORIGINS:", settings.CSRF_TRUSTED_ORIGINS)
```

### Common Issues

**400 Bad Request**: Domain not in `DJANGO_ALLOWED_HOSTS`

**403 CSRF Error**: Domain not in `DJANGO_CSRF_TRUSTED_ORIGINS` or protocol mismatch (http vs https)

**502 Bad Gateway**: Gunicorn not running - check `sudo systemctl status pillars`

**SSL Certificate Errors**: Run `sudo certbot renew --dry-run` to test renewal
