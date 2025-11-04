# -*- coding: utf-8 -*-
"""
Pre-migration script for Records Management 18.0.0.2.6

STRATEGY: Staged Module Loading (Two-Phase Upgrade)

PHASE 1 (THIS VERSION - 18.0.0.2.6):
- Disable records_location model temporarily
- Let stock.location load and fix its own parent_path naturally
- Odoo will recompute all stock_location hierarchies without interference

PHASE 2 (NEXT VERSION - 18.0.0.2.7):
- Re-enable records_location model
- Inherit from clean, working stock.location
- No MissingError because parent_path is already fixed

This avoids the chicken-and-egg problem where:
- records_location inherits stock.location
- stock.location has broken parent_path
- Odoo fails before we can fix anything
"""

def migrate(cr, version):
    """
    Phase 1: Let stock.location heal itself.
    
    Args:
        cr: Database cursor
        version: Current module version
    """
    print("🔧 PRE-Migration 18.0.0.2.6: PHASE 1 - Staged Loading")
    print("   → records_location temporarily disabled")
    print("   → stock.location will load and fix parent_path")
    print("   → Next version will re-enable records_location")
    
    # Clear parent_path and warehouse_id as before
    # This ensures stock.location can recompute cleanly
    
    # 1. Clear all parent_path values
    cr.execute("""
        UPDATE stock_location
        SET parent_path = NULL
    """)
    
    if cr.rowcount > 0:
        print(f"✅ Cleared parent_path for {cr.rowcount} locations")
    
    # 2. Clear warehouse_id (will be recomputed)
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
            print(f"✅ Cleared warehouse_id for {cr.rowcount} locations")
    
    print("✅ PHASE 1 Complete: stock.location ready to load")
    print("   Next: Version 18.0.0.2.7 will re-enable records_location")
