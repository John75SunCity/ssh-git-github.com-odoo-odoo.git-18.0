#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
until pg_isready -h "$HOST" -U "$USER"; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done

# Start SSH agent and add keys
if [ -f /root/.ssh/id_ed25519 ]; then
  eval $(ssh-agent -s)
  ssh-add /root/.ssh/id_ed25519
fi

# Start Odoo
exec "$@"
