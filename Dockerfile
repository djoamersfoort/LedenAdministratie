FROM python:3.5-alpine

# Set the file maintainer (your name - the file's author)
MAINTAINER Rients Brandsma

COPY LedenAdministratie/requirements.txt /srv/LedenAdministratie/requirements.txt

RUN apk update && \
    apk add nginx mariadb-dev zlib-dev gcc musl-dev jpeg-dev freetype-dev libffi-dev cairo-dev pango-dev ttf-dejavu && \
    pip3 install --no-cache-dir -r /srv/LedenAdministratie/requirements.txt && \
    apk del gcc musl-dev

WORKDIR /srv
RUN mkdir static logs /run/nginx

COPY nginx.conf /etc/nginx/nginx.conf

# Port to expose
EXPOSE 80

COPY LedenAdministratie /srv/LedenAdministratie

# Copy entrypoint script into the image
WORKDIR /srv/LedenAdministratie
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
