#!/usr/bin/env python3
"""
Odoo Shell Script to add missing res_partner columns
Run this via: odoo-bin shell -d <database> < add_partner_columns.py

Or connect to Odoo.sh shell and run:
    from odoo import sql_db
    cr = sql_db.db_connect('<dbname>').cursor()
    exec(open('add_partner_columns.py').read())
"""

import logging

_logger = logging.getLogger(__name__)


def add_missing_columns(cr):
    """Add missing res_partner columns for transitory configuration."""
    
    columns_to_add = [
        ('transitory_field_config_id', 'INTEGER', None),
        ('field_label_config_id', 'INTEGER', None),
        ('allow_transitory_items', 'BOOLEAN', True),
        ('max_transitory_items', 'INTEGER', 100),
    ]
    
    for column_name, column_type, default_value in columns_to_add:
        # Check if column exists
        cr.execute("""
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'res_partner' 
            AND column_name = %s
        """, (column_name,))
        
        if not cr.fetchone():
            print(f"➕ Adding column: res_partner.{column_name} ({column_type})")
            cr.execute(f'ALTER TABLE res_partner ADD COLUMN {column_name} {column_type}')
            
            if default_value is not None:
                print(f"🔧 Setting default value: {default_value}")
                cr.execute(
                    f'UPDATE res_partner SET {column_name} = %s WHERE {column_name} IS NULL',
                    (default_value,)
                )
            print(f"✅ Column res_partner.{column_name} added successfully")
        else:
            print(f"⏭️  Column res_partner.{column_name} already exists")
    
    cr.commit()
    print("\n✅ All columns processed successfully!")
    print("\nYou can now upgrade the records_management module.")


# If running via Odoo shell, env and cr are available
if 'env' in globals():
    add_missing_columns(env.cr)
# If running standalone with cr
elif 'cr' in globals():
    add_missing_columns(cr)
else:
    print("❌ This script must be run via Odoo shell")
    print("Usage: odoo-bin shell -d <database> < add_partner_columns.py")
