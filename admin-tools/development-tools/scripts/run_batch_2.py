#!/usr/bin/env python3
"""
🚀 BATCH 2 RUNNER - Ultimate Batch Fixer
========================================
Runs the second strategic batch to add 34 more critical fixes.
Execute this after Batch 1 deploys successfully.
"""

import sys
import os
sys.path.append('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')

from development_tools.ultimate_batch_fixer import UltimateBatchFixer

def run_batch_2():
    """Execute Batch 2 processing"""
    
    print("🚀 EXECUTING BATCH 2 - STRATEGIC FIELD & ACTION FIXES")
    print("=" * 60)
    
    # Change to correct directory
    if os.path.exists('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'):
        os.chdir('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')
    
    fixer = UltimateBatchFixer()
    
    # Re-scan to get current state
    fixer.scan_python_models()
    fixer.scan_xml_views()
    fixer.analyze_gaps()
    
    # Create batches (this will be the same as before)
    batches = fixer.create_batch_fixes()
    
    if len(batches) >= 2:
        # Apply Batch 2 (index 1)
        batch_2_models = batches[1]
        fixer.apply_batch_fixes(batch_2_models, 2)
        
        print(f"\n🚀 BATCH 2 COMPLETE!")
        print(f"✅ Fixed issues in {len(batch_2_models)} models")
        print(f"📦 {len(batches)-2} more batches remaining")
        print("\n🎯 NEXT STEPS:")
        print("1. Commit and push these Batch 2 changes")
        print("2. Wait for Odoo.sh deployment (10-15 min)")  
        print("3. Check for errors, then run Batch 3")
        
        return True
    else:
        print("❌ Batch 2 not available. Check Batch 1 deployment first.")
        return False

if __name__ == "__main__":
    run_batch_2()
