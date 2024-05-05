#
# Build image to create venv
#
FROM python:3.11-alpine AS build

# Set the file maintainer (your name - the file's author)
MAINTAINER Ronald Moesbergen

COPY requirements.txt /srv/requirements.txt

RUN apk update && \
    apk add mariadb-dev zlib-dev gcc musl-dev jpeg-dev freetype-dev libffi-dev cairo-dev pango-dev cargo

RUN pip3 install --upgrade pip virtualenv && \
    virtualenv /srv/venv && source /srv/venv/bin/activate && \
    pip3 install --no-cache-dir -r /srv/requirements.txt

#
# Runtime image
#
FROM python:3.11-alpine

RUN apk update && \
    apk add nginx mariadb-connector-c zlib jpeg freetype libffi pango ttf-dejavu dumb-init

WORKDIR /srv
RUN mkdir public logs venv

# Port to expose
EXPOSE 80

# Copy venv from build image
COPY --from=build /srv/venv /srv/venv
COPY deploy/nginx.conf /etc/nginx/nginx.conf

COPY static /srv/static
COPY templates /srv/templates
COPY LedenAdministratie /srv/LedenAdministratie
COPY manage.py /srv

# Copy entrypoint script into the image
COPY deploy/docker-entrypoint.sh /
COPY deploy/jobs.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
