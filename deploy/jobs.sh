#!/usr/bin/env sh

. /srv/venv/bin/activate

while true; do
  echo "[$(date)] Cleaning old sessions."
  python manage.py clearsessions
  echo "[$(date)] Cleaning old oauth tokens."
  python manage.py cleartokens
  echo "[$(date)] Cleaning old email logs."
  python manage.py purge_mail_log -r all 90
  echo "{$(date)] Syncing Stripcards."
  python manage.py sync_stripcards
  sleep 3600
done
