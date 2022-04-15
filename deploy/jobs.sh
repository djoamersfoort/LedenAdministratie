#!/usr/bin/env sh

source /srv/venv/bin/activate

while true; do
  echo "[$(date)] Cleaning old sessions."
  python manage.py clearsessions
  echo "[$(date)] Cleaning old oauth tokens."
  python manage.py cleartokens
  sleep 3600
done
