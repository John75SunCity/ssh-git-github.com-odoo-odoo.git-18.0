#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -h "$HOST" -U "$USER"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Start Odoo
exec "$@"
