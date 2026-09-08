# Deploying to dev.himalayanleaf.co

Assumes Ubuntu/Debian with systemd and nginx. The app runs as a dedicated
`himalayanleaf` system user (created in step 2 below); adjust `User=`/`Group=` in
`himalayanleaf.service` and `.socket` if you pick a different name. The VPS is a
shared box (`ssh padhaisewa` lands you as root) that already hosts other sites
under nginx 1.24, so nothing here removes or replaces existing site configs.

Layout this produces:

```
/srv/himalayanleaf/          the git checkout (web/ is the Django project)
/srv/himalayanleaf/venv/     virtualenv
/etc/himalayanleaf/env       secrets — root:himalayanleaf, chmod 640
/var/lib/himalayanleaf/      SQLite database + uploaded media (survives deploys)
/run/himalayanleaf/          gunicorn socket
```

## Heads-up: the domain is behind Cloudflare

`dev.himalayanleaf.co` resolves to Cloudflare (104.21.56.231), so the origin is
proxied. Two consequences:

- **Issuing the certificate.** Cloudflare forwards port 80, so certbot's HTTP-01
  challenge works while proxied. If it fails, grey-cloud (DNS-only) the
  `dev` record in Cloudflare, issue, then turn the proxy back on.
- **SSL mode.** Set the Cloudflare SSL/TLS mode for this hostname to **Full
  (strict)** once the Let's Encrypt cert is in place. "Flexible" would talk plain
  HTTP to the origin and put you in a redirect loop against `SECURE_SSL_REDIRECT`.

Cloudflare also caches aggressively. `collectstatic` writes hashed filenames so
CSS/JS changes bust themselves, but purge the cache after the first deploy.

## First time

```bash
# 1. packages
sudo apt update
sudo apt install -y python3-venv python3-pip nginx git certbot python3-certbot-nginx

# 2. service user + checkout
sudo useradd --system --home-dir /srv/himalayanleaf --no-create-home \
    --shell /usr/sbin/nologin --gid www-data himalayanleaf
sudo mkdir -p /srv/himalayanleaf
sudo chown himalayanleaf:www-data /srv/himalayanleaf
sudo -u himalayanleaf git clone https://github.com/AashishDhakal/himalayanleaf.git /srv/himalayanleaf
sudo git config --system --add safe.directory /srv/himalayanleaf   # so root can run git here too
cd /srv/himalayanleaf

# 3. virtualenv (as the service user, so the checkout stays owned by it)
sudo -u himalayanleaf -H python3 -m venv venv
sudo -u himalayanleaf -H ./venv/bin/pip install --upgrade pip
sudo -u himalayanleaf -H ./venv/bin/pip install -r web/requirements.txt

# 4. secrets
sudo mkdir -p /etc/himalayanleaf
sudo cp web/deploy/env.example /etc/himalayanleaf/env
./venv/bin/python -c "from django.utils.crypto import get_random_string as r; print(r(64, \"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\"))"
sudo nano /etc/himalayanleaf/env          # paste the key into DJANGO_SECRET_KEY
# The key generator above is deliberately alphanumeric: this file is both a systemd
# EnvironmentFile and `source`d by deploy.sh, and Django's default generator emits
# characters like `(` and `$` that break the latter.
sudo chown root:www-data /etc/himalayanleaf/env
sudo chmod 640 /etc/himalayanleaf/env

# 5. writable state
sudo mkdir -p /var/lib/himalayanleaf/media
sudo chown -R himalayanleaf:www-data /var/lib/himalayanleaf
sudo chmod 750 /var/lib/himalayanleaf

# 6. database, static files, admin login — as the service user, or the SQLite file
#    ends up owned by root and gunicorn cannot write it
sudo -u himalayanleaf -H bash -c '
  set -a; source /etc/himalayanleaf/env; set +a
  ./venv/bin/python web/manage.py migrate
  ./venv/bin/python web/manage.py collectstatic --noinput
  ./venv/bin/python web/manage.py createsuperuser
'

# 7. service
sudo cp web/deploy/himalayanleaf.socket web/deploy/himalayanleaf.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now himalayanleaf.socket himalayanleaf
systemctl status himalayanleaf --no-pager

# 8. nginx — HTTP first, so certbot has something to work with. nginx.conf
#    references certs that do not exist yet, so `nginx -t` rejects it until
#    certbot has run; stage a port-80-only block first.
sudo mkdir -p /var/www/certbot
sudo tee /etc/nginx/sites-available/dev.himalayanleaf.co >/dev/null <<'NG'
server {
    listen 80; listen [::]:80;
    server_name dev.himalayanleaf.co;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 404; }
}
NG
sudo ln -sf /etc/nginx/sites-available/dev.himalayanleaf.co /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot certonly --webroot -w /var/www/certbot -d dev.himalayanleaf.co

# Now the real config:
sudo cp web/deploy/nginx.conf /etc/nginx/sites-available/dev.himalayanleaf.co
sudo nginx -t && sudo systemctl reload nginx
```

If `certbot certonly --webroot` cannot reach the challenge (Cloudflare in the
way), temporarily grey-cloud the record, or use the DNS challenge:

```bash
sudo certbot certonly --manual --preferred-challenges dns -d dev.himalayanleaf.co
```

Renewal is handled by the `certbot.timer` systemd unit that ships with the
package — `systemctl list-timers certbot.timer` to confirm.

## Every deploy after that

```bash
sudo -u himalayanleaf /srv/himalayanleaf/web/deploy/deploy.sh
```

It fetches, installs, migrates, collects static, runs `check --deploy`, restarts
the service and smoke-tests the live URL. `BRANCH=some-branch deploy.sh` to
deploy something other than `main`. The service user has no login shell, hence
`sudo -u`. Note it does `git reset --hard`, so anything edited in the checkout on
the VPS is lost — change deploy files in the repo and push.

The script calls `sudo systemctl restart`. Give the service user just that, via
`sudo visudo -f /etc/sudoers.d/himalayanleaf`:

```
himalayanleaf ALL=(root) NOPASSWD: /bin/systemctl restart himalayanleaf
```

## When something is wrong

```bash
journalctl -u himalayanleaf -n 100 --no-pager   # application logs
sudo nginx -t                                   # nginx config
sudo tail -f /var/log/nginx/error.log
systemctl status himalayanleaf.socket
```

- **502 from nginx** — gunicorn is down or the socket path/permissions are wrong.
  Check `systemctl status himalayanleaf` and that `/run/himalayanleaf/gunicorn.sock`
  exists and is group-`www-data`.
- **CSRF failures on the quote form** — `DJANGO_CSRF_TRUSTED_ORIGINS` must include
  `https://dev.himalayanleaf.co`, and nginx must pass `X-Forwarded-Proto`.
- **Redirect loop** — Cloudflare SSL mode is "Flexible"; set it to Full (strict).
- **Stale CSS** — purge the Cloudflare cache; hashed filenames handle it after that.

## Before this becomes the real site

`DEBUG=0`, the secret key and TLS are handled above, but two things from the
build are still open and are not deployment problems: the photography is CC BY-SA
stand-ins requiring attribution, and the commercial figures are placeholders. See
`../README.md`.
