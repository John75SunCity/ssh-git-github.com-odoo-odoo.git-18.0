# -*- coding: utf-8 -*-
"""
Pre-migration script for Records Management 18.0.0.2.0

CHANGE: location_id field changed from records.location to stock.location

ISSUE:
- Existing containers have location_id values pointing to records.location (old)
- New field definition points to stock.location (native Odoo)
- Foreign key constraint fails because IDs don't exist in stock_location table

SOLUTION:
- Clear location_id values before model loads
- Containers will be assigned stock.location after activation
- Stock.quant creation will populate current_location_id (related field)

This is safe because:
1. Module is not live in production
2. Location data will be recreated via stock integration
3. current_location_id (related to quant_id.location_id) is the real source of truth
"""

def migrate(cr, version):
    """
    Clear location_id values to allow field type change.
    
    Args:
        cr: Database cursor
        version: Current module version
    """
    if not version:
        return
    
    # Check if location_id column exists and has data
    cr.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'records_container' 
            AND column_name = 'location_id'
        )
    """)
    
    if cr.fetchone()[0]:
        # Clear location_id to allow foreign key constraint change
        cr.execute("""
            UPDATE records_container 
            SET location_id = NULL
            WHERE location_id IS NOT NULL
        """)
        
        # Log how many records were cleared
        cr.execute("SELECT COUNT(*) FROM records_container WHERE location_id IS NULL")
        count = cr.fetchone()[0]
        
        print(f"✅ Migration 18.0.0.2.0: Cleared location_id on {count} containers")
        print("   (Will be repopulated via stock integration)")
