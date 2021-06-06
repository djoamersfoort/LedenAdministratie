#!/usr/bin/env sh

while true; do
  python3 manage.py clearsessions
  python3 manage.py cleartokens
  sleep 3600
done
