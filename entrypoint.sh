#!/bin/bash
set -e

# Wait for the database to be available
until pg_isready -h "$HOST" -U "$USER"; do
  echo "Waiting for PostgreSQL at $HOST..."
  sleep 2
done

# Set default Odoo command if none is provided
if [ "$1" = "odoo" ] || [ "$1" = "./odoo.py" ] || [ -z "$1" ]; then
  exec python ./odoo.py --addons-path=/mnt/extra-addons,/addons "$@"
else
  exec "$@"
fi
