#!/usr/bin/env sh

while true; do
  echo "[$(date)] Cleaning old sessions."
  python3 manage.py clearsessions
  echo "[$(date)] Cleaning old oauth tokens."
  python3 manage.py cleartokens
  sleep 3600
done
