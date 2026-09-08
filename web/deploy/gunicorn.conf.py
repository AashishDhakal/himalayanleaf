"""Gunicorn config for Himalayan Leaf.

Referenced by the systemd unit. nginx talks to the unix socket below.
"""

import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "unix:/run/himalayanleaf/gunicorn.sock")

# The site is I/O-light and CPU-light; 2·cores+1 is the usual starting point,
# capped so a small VPS is not oversubscribed.
workers = int(os.environ.get("GUNICORN_WORKERS", min(multiprocessing.cpu_count() * 2 + 1, 5)))
threads = int(os.environ.get("GUNICORN_THREADS", 2))

timeout = 30
graceful_timeout = 30
keepalive = 5

# Recycle workers to keep any slow leak from accumulating.
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")
# Log the forwarded client IP rather than nginx's.
access_log_format = '%({x-forwarded-for}i)s %(m)s %(U)s %(s)s %(L)ss'

forwarded_allow_ips = "*"  # only nginx on localhost can reach the socket

# gunicorn 26 opens a control socket, defaulting to $HOME/.gunicorn, which is
# read-only under the unit's ProtectSystem=strict. Keep it in the RuntimeDirectory.
control_socket = os.environ.get("GUNICORN_CONTROL_SOCKET", "/run/himalayanleaf/gunicorn.ctl")
