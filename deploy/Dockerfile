FROM python:3.8-alpine

# Set the file maintainer (your name - the file's author)
MAINTAINER Ronald Moesbergen

COPY requirements.txt /srv/requirements.txt

RUN apk update && \
    apk add nginx mariadb-dev zlib-dev gcc musl-dev jpeg-dev freetype-dev libffi-dev cairo-dev pango-dev ttf-dejavu cargo && \
    pip3 install --upgrade pip && \
    pip3 install --no-cache-dir -r /srv/requirements.txt && \
    apk del gcc musl-dev rust cargo

WORKDIR /srv
RUN mkdir public logs

COPY deploy/nginx.conf /etc/nginx/nginx.conf

# Port to expose
EXPOSE 80

COPY static /srv/static
COPY LedenAdministratie /srv/LedenAdministratie
COPY manage.py /srv

# Copy entrypoint script into the image
COPY deploy/docker-entrypoint.sh /
COPY deploy/jobs.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
