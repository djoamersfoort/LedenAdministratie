# Set the base image to use to Ubuntu
FROM ubuntu:16.04

# Set the file maintainer (your name - the file's author)
MAINTAINER Ronald Moesbergen

ENV LEDEN_SRC=LedenAdministratie
ENV LEDEN_SRVHOME=/srv
ENV LEDEN_SRVPROJ=/srv/LedenAdministratie

RUN apt-get update && apt-get install -y libmysqlclient-dev python3-pip

WORKDIR $LEDEN_SRVHOME
RUN mkdir static logs

COPY $LEDEN_SRC $LEDEN_SRVPROJ

RUN pip3 install -r $LEDEN_SRVPROJ/requirements.txt

# Port to expose
EXPOSE 8000

# Copy entrypoint script into the image
WORKDIR $LEDEN_SRVPROJ
COPY ./docker-entrypoint.sh /
ENTRYPOINT ["/docker-entrypoint.sh"]
