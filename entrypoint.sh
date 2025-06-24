#!/bin/bash

# Start PostgreSQL
service postgresql start

# Start Odoo
exec odoo
