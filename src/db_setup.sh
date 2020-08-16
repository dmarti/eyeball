#!/bin/bash

set -e
set -x

trap popd EXIT
pushd $PWD
cd $(dirname "$0")

cp pg_hba.conf /etc/postgresql/9.6/main
service postgresql restart

# create the database if it does not exist already
echo "SELECT 'CREATE DATABASE eyeball' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'eyeball')\gexec" | psql --user postgres

[ -e db_dump.sql ] && psql --user postgres eyeball < db_dump.sql
psql --user postgres -d eyeball -f schema.sql

