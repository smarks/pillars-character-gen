# HTTPS Setup Notes

This documents the setup of HTTPS for pillars.duckdns.org.

## Domain Setup (DuckDNS)

1. Created free subdomain at https://www.duckdns.org: `pillars.duckdns.org`
2. Points to public IP: `97.80.103.132`

### Auto-updater Script

Location: `~/duckdns/duck.sh`

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=pillars&token=YOUR-TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

Runs every 5 minutes via cron to keep IP updated.

## Port Forwarding

On router, forwarded:
- Port 80 → 192.168.4.163:80
- Port 443 → 192.168.4.163:443

## Nginx Configuration

Location: `/etc/nginx/sites-available/pillars`

```nginx
server {
    listen 80;
    server_name pillars.duckdns.org;

    location / {
        proxy_pass http://127.0.0.1:9066;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/sam/dev/pillars-character-gen/webapp/staticfiles/;
    }
}
```

Enabled with:
```bash
sudo ln -sf /etc/nginx/sites-available/pillars /etc/nginx/sites-enabled/pillars
```

## SSL Certificate (Let's Encrypt)

Installed with Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d pillars.duckdns.org
```

Certbot automatically:
- Obtained the SSL certificate
- Modified nginx config for HTTPS
- Set up auto-renewal (runs via systemd timer)

Check renewal status:
```bash
sudo certbot certificates
sudo certbot renew --dry-run
```

## Django Configuration

Updated `.env`:

```bash
DJANGO_ALLOWED_HOSTS=pillars.duckdns.org,97.80.103.132,192.168.4.163
DJANGO_CSRF_TRUSTED_ORIGINS=https://pillars.duckdns.org,http://97.80.103.132:9066,http://192.168.4.163:9066
DJANGO_USE_HTTPS=True
```

## Architecture

```
Internet
    │
    ▼
Router (port forward 80/443)
    │
    ▼
Nginx (192.168.4.163:80/443)
    │ SSL termination
    ▼
Gunicorn (127.0.0.1:9066)
    │
    ▼
Django App
```

## URLs

- **Public HTTPS**: https://pillars.duckdns.org
- **Local HTTP**: http://192.168.4.163:9066

## Maintenance

Restart services:
```bash
sudo systemctl restart pillars
sudo systemctl reload nginx
```

Check status:
```bash
sudo systemctl status pillars
sudo systemctl status nginx
```

View logs:
```bash
sudo journalctl -u pillars -f
sudo tail -f /var/log/nginx/error.log
```
