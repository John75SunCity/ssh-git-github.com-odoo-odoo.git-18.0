# -*- coding: utf-8 -*-
"""
Pre-migration script for Records Management 18.0.0.2.1

ISSUE: MissingError for stock.location during module upgrade

ROOT CAUSE:
- Module tries to load and compute warehouse_id for stock.location records
- Some warehouses reference deleted stock.location records (ID 36, 255, etc.)
- Odoo fails BEFORE post-migration can run

SOLUTION:
- Clean up orphaned warehouse references BEFORE module loads
- This runs at SQL level, before any Python model loading
- Allows module upgrade to proceed

CRITICAL: This must be PRE-migration to run before model loading
"""

def migrate(cr, version):
    """
    Clean up orphaned stock.location references before module loads.
    
    Args:
        cr: Database cursor
        version: Current module version
    """
    print("🔧 PRE-Migration 18.0.0.2.1: Cleaning orphaned location references...")
    
    # ============================================================================
    # 1. FIX WAREHOUSES WITH DELETED LOCATIONS
    # ============================================================================
    
    # Find warehouses with missing view_location_id
    cr.execute("""
        SELECT w.id, w.name, w.view_location_id
        FROM stock_warehouse w
        LEFT JOIN stock_location l ON w.view_location_id = l.id
        WHERE w.view_location_id IS NOT NULL 
        AND l.id IS NULL
    """)
    
    orphaned_warehouses = cr.fetchall()
    
    if orphaned_warehouses:
        print(f"⚠️  Found {len(orphaned_warehouses)} warehouses with deleted view locations:")
        for wh_id, wh_name, loc_id in orphaned_warehouses:
            print(f"   - Warehouse '{wh_name}' (ID {wh_id}) → Missing location {loc_id}")
        
        # Get a valid physical location to use as fallback
        cr.execute("""
            SELECT id FROM stock_location 
            WHERE usage = 'internal' 
            AND active = true
            ORDER BY id
            LIMIT 1
        """)
        
        fallback = cr.fetchone()
        
        if fallback:
            fallback_id = fallback[0]
            
            # Update all orphaned warehouses
            cr.execute("""
                UPDATE stock_warehouse w
                SET view_location_id = %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM stock_location l 
                    WHERE l.id = w.view_location_id
                )
                AND w.view_location_id IS NOT NULL
            """, (fallback_id,))
            
            print(f"✅ Updated {cr.rowcount} warehouses to use location {fallback_id}")
        else:
            # No valid location - set to NULL (Odoo will handle on creation)
            cr.execute("""
                UPDATE stock_warehouse w
                SET view_location_id = NULL
                WHERE NOT EXISTS (
                    SELECT 1 FROM stock_location l 
                    WHERE l.id = w.view_location_id
                )
                AND w.view_location_id IS NOT NULL
            """)
            
            print(f"⚠️  Set {cr.rowcount} warehouse view_location_id to NULL")
    
    # ============================================================================
    # 2. FIX WAREHOUSE LOT/INPUT/OUTPUT/PACKING LOCATIONS
    # ============================================================================
    
    # Check other warehouse location references
    location_fields = [
        'lot_stock_id',
        'wh_input_stock_loc_id', 
        'wh_qc_stock_loc_id',
        'wh_output_stock_loc_id',
        'wh_pack_stock_loc_id'
    ]
    
    for field in location_fields:
        # Check if field exists (some might not in all Odoo versions)
        cr.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'stock_warehouse' 
            AND column_name = %s
        """, (field,))
        
        if cr.fetchone():
            cr.execute(f"""
                SELECT w.id, w.name, w.{field}
                FROM stock_warehouse w
                LEFT JOIN stock_location l ON w.{field} = l.id
                WHERE w.{field} IS NOT NULL 
                AND l.id IS NULL
            """)
            
            orphaned = cr.fetchall()
            
            if orphaned:
                print(f"⚠️  Found {len(orphaned)} warehouses with deleted {field}")
                
                # Set to NULL - Odoo will recreate on save
                cr.execute(f"""
                    UPDATE stock_warehouse w
                    SET {field} = NULL
                    WHERE NOT EXISTS (
                        SELECT 1 FROM stock_location l 
                        WHERE l.id = w.{field}
                    )
                    AND w.{field} IS NOT NULL
                """)
                
                print(f"✅ Cleared {cr.rowcount} orphaned {field} references")
    
    # ============================================================================
    # 3. FIX LOCATION PARENT REFERENCES
    # ============================================================================
    
    # Find locations with deleted parent (location_id)
    cr.execute("""
        SELECT l.id, l.name, l.location_id
        FROM stock_location l
        LEFT JOIN stock_location parent ON l.location_id = parent.id
        WHERE l.location_id IS NOT NULL
        AND parent.id IS NULL
    """)
    
    orphaned_children = cr.fetchall()
    
    if orphaned_children:
        print(f"⚠️  Found {len(orphaned_children)} locations with deleted parents:")
        for loc_id, loc_name, parent_id in orphaned_children:
            print(f"   - Location '{loc_name}' (ID {loc_id}) → Missing parent {parent_id}")
        
        # Get root location (no parent)
        cr.execute("""
            SELECT id FROM stock_location 
            WHERE location_id IS NULL 
            AND usage = 'view'
            AND active = true
            ORDER BY id
            LIMIT 1
        """)
        
        root = cr.fetchone()
        
        if root:
            root_id = root[0]
            
            # Re-parent orphaned locations to root
            cr.execute("""
                UPDATE stock_location l
                SET location_id = %s
                WHERE NOT EXISTS (
                    SELECT 1 FROM stock_location parent
                    WHERE parent.id = l.location_id
                )
                AND l.location_id IS NOT NULL
            """, (root_id,))
            
            print(f"✅ Re-parented {cr.rowcount} locations to root location {root_id}")
        else:
            # Set to NULL (make them root locations)
            cr.execute("""
                UPDATE stock_location l
                SET location_id = NULL
                WHERE NOT EXISTS (
                    SELECT 1 FROM stock_location parent
                    WHERE parent.id = l.location_id
                )
                AND l.location_id IS NOT NULL
            """)
            
            print(f"⚠️  Set {cr.rowcount} locations to root level (no parent)")
    
    # ============================================================================
    # 4. CLEAR BROKEN PARENT_PATH ENTRIES
    # ============================================================================
    
    # CRITICAL: Clear ALL parent_path values FIRST
    # This prevents MissingError when Odoo tries to traverse paths
    # Odoo will recompute all hierarchies after module loads
    cr.execute("""
        UPDATE stock_location
        SET parent_path = NULL
    """)
    
    if cr.rowcount > 0:
        print(f"✅ Cleared parent_path for {cr.rowcount} locations (will be recomputed)")
    
    # Also ensure warehouse_id is cleared (will be recomputed)
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'stock_location' 
        AND column_name = 'warehouse_id'
    """)
    
    if cr.fetchone():
        cr.execute("""
            UPDATE stock_location
            SET warehouse_id = NULL
        """)
        
        if cr.rowcount > 0:
            print(f"✅ Cleared warehouse_id for {cr.rowcount} locations (will be recomputed)")
    
    # ============================================================================
    # 5. SUMMARY
    # ============================================================================
    
    print("✅ PRE-Migration 18.0.0.2.1: Database cleanup complete")
    print("   Module can now load without MissingError")
    print("   Odoo will recompute hierarchies and relationships")
