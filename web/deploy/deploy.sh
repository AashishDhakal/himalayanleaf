#!/usr/bin/env bash
#
# Repeat deploy. Run on the VPS as the service user:
#   /srv/himalayanleaf/web/deploy/deploy.sh
#
# First-time setup is in deploy/README.md — this script assumes it has been done.
set -euo pipefail

APP_DIR=${APP_DIR:-/srv/himalayanleaf}
BRANCH=${BRANCH:-main}
VENV="$APP_DIR/venv"
WEB="$APP_DIR/web"
HEALTH_URL=${HEALTH_URL:-https://dev.himalayanleaf.co/}

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }

say "Fetching $BRANCH"
git -C "$APP_DIR" fetch --prune origin
# --force: anything edited by hand in the checkout is discarded, same as the
# reset below — a stray local change must not be able to block a deploy.
git -C "$APP_DIR" checkout --force "$BRANCH"
before=$(git -C "$APP_DIR" rev-parse HEAD)
git -C "$APP_DIR" reset --hard "origin/$BRANCH"
after=$(git -C "$APP_DIR" rev-parse HEAD)
echo "$before -> $after"

say "Installing dependencies"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$WEB/requirements.txt"

# The env file carries DJANGO_SECRET_KEY and friends; management commands need
# them too, not just the service.
set -a
# shellcheck disable=SC1091
source /etc/himalayanleaf/env
set +a

say "Migrating"
"$VENV/bin/python" "$WEB/manage.py" migrate --noinput

say "Collecting static files"
"$VENV/bin/python" "$WEB/manage.py" collectstatic --noinput

say "Deployment checks"
"$VENV/bin/python" "$WEB/manage.py" check --deploy

say "Restarting"
sudo systemctl restart himalayanleaf
sleep 2
systemctl is-active --quiet himalayanleaf && echo "service active" || {
    echo "service failed to start:" >&2
    journalctl -u himalayanleaf -n 40 --no-pager >&2
    exit 1
}

say "Smoke test"
code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 20 "$HEALTH_URL" || echo 000)
echo "GET $HEALTH_URL -> $code"
[ "$code" = "200" ] || { echo "expected 200 — check journalctl -u himalayanleaf" >&2; exit 1; }

say "Deployed $after"
