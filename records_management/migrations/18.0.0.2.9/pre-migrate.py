# -*- coding: utf-8 -*-
"""
Pre-migration script for Records Management 18.0.0.2.9

FIX: Convert storage_capacity from formatted strings to integers

ISSUE: 
- User created locations with storage_capacity = "2,000,000" (string with commas)
- New field definition is Integer type
- PostgreSQL fails: invalid input syntax for type integer: "2,000,000"

SOLUTION:
- Remove commas and convert to integer before field type change
- Handle NULL values gracefully
- Preserve original capacity values
"""

def migrate(cr, version):
    """
    Clean up storage_capacity data before Integer field conversion.
    
    Args:
        cr: Database cursor
        version: Current module version
    """
    print("🔧 PRE-Migration 18.0.0.2.9: Fix storage_capacity formatting")
    
    # Check if storage_capacity column exists in records_location table
    cr.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns 
        WHERE table_name = 'records_location' 
        AND column_name = 'storage_capacity'
    """)
    
    result = cr.fetchone()
    
    if result:
        column_name, data_type = result
        print(f"   Found storage_capacity column: {data_type} type")
        
        # If it's a text/varchar column, clean up the data
        if data_type in ('character varying', 'text', 'varchar'):
            print("   Converting formatted strings to integers...")
            
            # Remove commas and convert to integer
            # Examples: "2,000,000" -> 2000000, "1,500" -> 1500
            cr.execute("""
                UPDATE records_location
                SET storage_capacity = 
                    CASE 
                        WHEN storage_capacity IS NULL OR storage_capacity = '' THEN '0'
                        ELSE REGEXP_REPLACE(storage_capacity, '[^0-9]', '', 'g')
                    END::integer
                WHERE storage_capacity IS NOT NULL
            """)
            
            print(f"   ✅ Cleaned {cr.rowcount} storage_capacity values")
            
            # Show some examples of what was converted
            # Cast to integer for comparison since we just converted the data
            cr.execute("""
                SELECT id, name, storage_capacity::integer 
                FROM records_location 
                WHERE storage_capacity::integer > 0
                ORDER BY storage_capacity::integer DESC
                LIMIT 5
            """)
            
            examples = cr.fetchall()
            if examples:
                print("   Examples of converted values:")
                for loc_id, loc_name, capacity in examples:
                    # capacity is already an integer from the query
                    print(f"      - {loc_name}: {capacity:,} containers")
    else:
        print("   ℹ️  storage_capacity column doesn't exist yet (will be created)")
    
    print("✅ PRE-Migration 18.0.0.2.9: Data cleanup complete")
