FROM jgoerzen/debian-base-security:stretch
ENV TERM linux
RUN apt-get update && \
    apt-get -y install postgresql python3-pip libpq-dev sudo && \
    apt-get -y clean && rm -rf /var/lib/apt/lists/*

RUN mkdir /srv/eyeball
COPY src/requirements.txt /srv/eyeball
RUN pip3 install -r /srv/eyeball/requirements.txt

COPY src/pg_hba.conf src/schema.sql src/db_setup.sh data/db_dump.sql* /srv/eyeball/
RUN /srv/eyeball/db_setup.sh
RUN service postgresql stop

ENTRYPOINT ["/bin/sh"]
