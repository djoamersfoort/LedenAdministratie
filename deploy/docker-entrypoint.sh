#!/usr/bin/dumb-init /bin/sh

# Activate python3 venv
. /srv/venv/bin/activate

python manage.py migrate                  # Apply database migrations
python manage.py collectstatic --noinput  # Collect static files

# Prepare log files and start outputting logs to stdout
touch /srv/logs/gunicorn.log
touch /srv/logs/access.log
tail -n 0 -f /srv/logs/*.log &

# Update font cache
/usr/bin/fc-cache

# Start nginx
nginx

# Start cleanup jobs in a loop
sh /jobs.sh &

# Start django-mailer queue processor
python manage.py runmailer &

# Start Gunicorn processes
echo "Starting Gunicorn."
gunicorn LedenAdministratie.wsgi:application \
    --name LedenAdministratie \
    --bind 0.0.0.0:8000 \
    --timeout 300 \
    --workers 3 \
    --log-level=info \
    --log-file=/srv/logs/gunicorn.log \
    --access-logfile=/srv/logs/access.log \
    "$@"
