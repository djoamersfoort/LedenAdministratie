# Set the base image to use to Ubuntu
FROM python:3.5-alpine

# Set the file maintainer (your name - the file's author)
MAINTAINER Ronald Moesbergen

RUN apk update && apk add nginx

WORKDIR /srv
RUN mkdir static logs

COPY LedenAdministratie /srv/LedenAdministratie

RUN pip3 install -r /srv/LedenAdministratie/requirements.txt

# Port to expose
EXPOSE 80

# Copy entrypoint script into the image
WORKDIR /srv/LedenAdministratie
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
