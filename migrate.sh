#!/bin/bash
set -e
# Bridge postgresql relation env to the name alembic/env.py expects
DATABASE_URL="${DATABASE_URL:-$POSTGRESQL_DB_CONNECT_STRING}"
export DATABASE_URL
alembic upgrade head
