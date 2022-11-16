#!/bin/sh
export PGPASSWORD=$POSTGRES_PASSWORD
if test -f /bitnami/postgresql/redash96dump.sql; then
echo "Load Dump"
psql -Uredash redash -f /bitnami/postgresql/redash96dump.sql
rm -rf /bitnami/postgresql/redash96dump.sql /bitnami/postgresql/data96
else
echo "Dump file not exist, skip and run Postgresql"
fi