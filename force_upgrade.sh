#!/bin/bash
# Force module upgrade via Odoo.sh CLI
# Run this in your Odoo.sh shell session

# Upgrade records_management module
odoo-bin -u records_management --stop-after-init

echo "✅ Module upgrade complete! Server will restart automatically."
