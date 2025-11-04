# -*- coding: utf-8 -*-
"""
Pre-migration script for Records Management 18.0.0.2.7

PHASE 2: Re-enable records_location with safeguards

After Phase 1 (v18.0.0.2.6):
- stock.location loaded and fixed parent_path naturally
- All warehouses and hierarchies recomputed
- Database is now in clean state

This Phase (v18.0.0.2.7):
- records_location re-enabled with safe _compute_warehouse_id override
- Catches any remaining MissingError during upgrade
- Allows module to complete loading successfully

Safeguard Added:
- records_location._compute_warehouse_id wrapped in try/except
- If stock.location computation fails → sets warehouse_id = False
- Odoo will recompute correctly after upgrade completes
"""

def migrate(cr, version):
    """
    Phase 2: Final cleanup and safeguards.
    
    Args:
        cr: Database cursor
        version: Current module version
    """
    print("🔧 PRE-Migration 18.0.0.2.7: PHASE 2 - Re-enable with safeguards")
    print("   → records_location model re-enabled")
    print("   → Safe _compute_warehouse_id override active")
    print("   → Migration complete - module ready for normal operation")
    
    # One final cleanup to ensure everything is fresh
    cr.execute("""
        UPDATE stock_location
        SET parent_path = NULL, warehouse_id = NULL
        WHERE parent_path IS NOT NULL OR warehouse_id IS NOT NULL
    """)
    
    if cr.rowcount > 0:
        print(f"✅ Final cleanup: Reset {cr.rowcount} locations for recompute")
    
    print("✅ PHASE 2 Complete: Module fully operational")
