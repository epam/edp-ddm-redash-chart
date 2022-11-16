#!/bin/bash

admin_pod=redash-admin-postgresql-0
viewer_pod=redash-viewer-postgresql-0
pg_ver=9.6
ctr_name=redash-chart-postgresql

AdminVer=$(oc exec $admin_pod -n $NAMESPACE -c $ctr_name -- bash -c 'cat $PGDATA/PG_VERSION')
ViewerVer=$(oc exec $viewer_pod -n $NAMESPACE -c $ctr_name -- bash -c 'cat $PGDATA/PG_VERSION')

# Admin PostgreSQL DB
if oc -n $NAMESPACE get secret redash-chart-postgresql 2> /dev/null && [ "$AdminVer" = "$pg_ver" ]; then oc exec $admin_pod -n $NAMESPACE -c $ctr_name \
-- bash -c 'export PGPASSWORD=$POSTGRES_PASSWORD; pg_dump -Uredash redash -c -f /bitnami/postgresql/redash96dump.sql && mv /bitnami/postgresql/data /bitnami/postgresql/data96'
fi
    
# Viewer PostgreSQL DB
if oc -n $NAMESPACE get secret redash-chart-postgresql 2> /dev/null && [ "$ViewerVer" = "$pg_ver" ]; then oc exec $viewer_pod -n $NAMESPACE -c $ctr_name \
-- bash -c 'export PGPASSWORD=$POSTGRES_PASSWORD; pg_dump -Uredash redash -c -f /bitnami/postgresql/redash96dump.sql && mv /bitnami/postgresql/data /bitnami/postgresql/data96'
fi
