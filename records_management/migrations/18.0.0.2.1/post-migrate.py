# -*- coding: utf-8 -*-
"""
Post-migration script for Records Management 18.0.0.2.1

ISSUE: MissingError for stock.location(255) during warehouse computation

ROOT CAUSE:
- Deleted stock.location records still referenced by warehouses
- Orphaned parent_path references in location hierarchy
- Stale data from previous testing/migrations

SOLUTION:
- Clean up orphaned warehouse references
- Fix broken location hierarchies
- Remove invalid parent_path entries

This prevents MissingError during module loading.
"""

def migrate(cr, version):
    """
    Clean up orphaned stock.location references.
    
    Args:
        cr: Database cursor
        version: Current module version
    """
    if not version:
        return
    
    print("🔧 Migration 18.0.0.2.1: Cleaning orphaned location references...")
    
    # 1. Find and fix warehouses with deleted view_location_id
    cr.execute("""
        SELECT w.id, w.name, w.view_location_id
        FROM stock_warehouse w
        LEFT JOIN stock_location l ON w.view_location_id = l.id
        WHERE w.view_location_id IS NOT NULL 
        AND l.id IS NULL
    """)
    
    orphaned_warehouses = cr.fetchall()
    
    if orphaned_warehouses:
        print(f"⚠️  Found {len(orphaned_warehouses)} warehouses with deleted locations:")
        for wh_id, wh_name, loc_id in orphaned_warehouses:
            print(f"   - Warehouse '{wh_name}' (ID {wh_id}) → Missing location {loc_id}")
        
        # Get a valid view location (or create one)
        cr.execute("""
            SELECT id FROM stock_location 
            WHERE usage = 'view' 
            AND active = true
            LIMIT 1
        """)
        
        fallback_location = cr.fetchone()
        
        if fallback_location:
            fallback_id = fallback_location[0]
            
            # Update orphaned warehouses to use valid location
            cr.execute("""
                UPDATE stock_warehouse w
                SET view_location_id = %s
                WHERE view_location_id IN (
                    SELECT w2.view_location_id
                    FROM stock_warehouse w2
                    LEFT JOIN stock_location l ON w2.view_location_id = l.id
                    WHERE l.id IS NULL
                )
            """, (fallback_id,))
            
            print(f"✅ Updated {cr.rowcount} warehouses to use location {fallback_id}")
        else:
            # No valid view location - set to NULL to allow warehouse creation
            cr.execute("""
                UPDATE stock_warehouse w
                SET view_location_id = NULL
                WHERE view_location_id IN (
                    SELECT w2.view_location_id
                    FROM stock_warehouse w2
                    LEFT JOIN stock_location l ON w2.view_location_id = l.id
                    WHERE l.id IS NULL
                )
            """)
            
            print(f"⚠️  Set {cr.rowcount} warehouse view_location_id to NULL (will auto-create)")
    
    # 2. Fix broken parent_path references
    cr.execute("""
        SELECT id, name, parent_path
        FROM stock_location
        WHERE parent_path IS NOT NULL
        AND parent_path != ''
    """)
    
    locations_with_paths = cr.fetchall()
    broken_paths = []
    
    for loc_id, loc_name, parent_path in locations_with_paths:
        # Extract all location IDs from path (format: /123/456/789/)
        path_ids = [int(x) for x in parent_path.split('/') if x.isdigit()]
        
        # Check if all path IDs exist
        if path_ids:
            cr.execute("""
                SELECT id FROM stock_location WHERE id = ANY(%s)
            """, (path_ids,))
            
            existing_ids = {row[0] for row in cr.fetchall()}
            missing_ids = set(path_ids) - existing_ids
            
            if missing_ids:
                broken_paths.append((loc_id, loc_name, missing_ids))
    
    if broken_paths:
        print(f"⚠️  Found {len(broken_paths)} locations with broken parent_path:")
        for loc_id, loc_name, missing in broken_paths:
            print(f"   - Location '{loc_name}' (ID {loc_id}) → Missing parents: {missing}")
        
        # Recompute parent_path for affected locations
        # This is safe - Odoo will rebuild the hierarchy
        affected_ids = [loc_id for loc_id, _, _ in broken_paths]
        
        cr.execute("""
            UPDATE stock_location 
            SET parent_path = NULL
            WHERE id = ANY(%s)
        """, (affected_ids,))
        
        print(f"✅ Cleared parent_path for {cr.rowcount} locations (will be recomputed)")
    
    # 3. Summary
    print("✅ Migration 18.0.0.2.1: Orphaned reference cleanup complete")
    
    if not orphaned_warehouses and not broken_paths:
        print("   No orphaned references found - database is clean!")
