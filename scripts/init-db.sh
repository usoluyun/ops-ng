#!/usr/bin/env bash
set -e

# Wait for PostgreSQL to be ready
until psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -c '\l' > /dev/null 2>&1; do
  echo "Waiting for PostgreSQL to be ready..."
  sleep 1
done

# Create databases for Strapi and Hydra
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    CREATE DATABASE strapi_db;
    CREATE DATABASE hydra_db;
EOSQL

echo "Databases strapi_db and hydra_db created successfully."