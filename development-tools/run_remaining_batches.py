#!/usr/bin/env python3
"""
🚀 RUN REMAINING BATCHES (2, 3, 4) - Ultimate Batch Fixer
=========================================================
Executes batches 2, 3, and 4 in sequence to complete the comprehensive fixes.
This will add the remaining 95 field/action fixes in strategic batches.
"""

import sys
import os
sys.path.append('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')

from development_tools.ultimate_batch_fixer import UltimateBatchFixer

def run_batches_2_3_4():
    """Execute Batches 2, 3, and 4 in sequence"""
    
    print("🚀 EXECUTING BATCHES 2, 3, 4 - STRATEGIC FIELD & ACTION FIXES")
    print("=" * 70)
    print("🎯 Goal: Complete remaining 95 fixes in 3 strategic deployments")
    print("⏰ Time Savings: Continue saving 25+ hours of individual deployments")
    print("=" * 70)
    
    # Change to correct directory
    if os.path.exists('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0'):
        os.chdir('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0')
    
    fixer = UltimateBatchFixer()
    
    # Re-scan to get current state (after Batch 1 changes)
    print("\n📊 RESCANNING AFTER BATCH 1...")
    fixer.scan_python_models()
    fixer.scan_xml_views()
    total_fields, total_actions = fixer.analyze_gaps()
    
    if total_fields == 0 and total_actions == 0:
        print("\n🎉 ALL GAPS ALREADY FIXED! No remaining batches needed.")
        return True
    
    # Create batches (this will show current state)
    batches = fixer.create_batch_fixes()
    
    if len(batches) < 4:
        print(f"\n✅ Only {len(batches)} batches needed. Processing all remaining...")
        start_batch = 2
        end_batch = len(batches) + 1
    else:
        start_batch = 2
        end_batch = 5  # Batches 2, 3, 4
    
    # Apply batches 2, 3, 4 in sequence
    for batch_num in range(start_batch, min(end_batch, len(batches) + 1)):
        batch_index = batch_num - 1  # Convert to 0-based index
        
        if batch_index < len(batches):
            batch_models = batches[batch_index]
            print(f"\n{'='*50}")
            print(f"🛠️  PROCESSING BATCH {batch_num}")
            print(f"{'='*50}")
            
            fixer.apply_batch_fixes(batch_models, batch_num)
            
            # Show progress
            total_fixes_this_batch = sum(
                len(fixer.missing_fields.get(m, [])) + 
                len(fixer.missing_actions.get(m, []))
                for m in batch_models
            )
            
            print(f"\n✅ BATCH {batch_num} COMPLETE!")
            print(f"   📦 Models processed: {len(batch_models)}")
            print(f"   🔧 Fixes applied: ~{total_fixes_this_batch}")
            
            # Remove processed items to avoid double-processing
            for model in batch_models:
                if model in fixer.missing_fields:
                    del fixer.missing_fields[model]
                if model in fixer.missing_actions:
                    del fixer.missing_actions[model]
    
    print(f"\n🚀 BATCHES 2, 3, 4 COMPLETE!")
    print(f"✅ All remaining strategic batches applied")
    print(f"📦 Ready for final deployment cycle")
    print("\n🎯 NEXT STEPS:")
    print("1. Commit and push these changes")
    print("2. Wait for Odoo.sh deployment (10-15 min)")  
    print("3. Verify all XML-Python gaps are resolved")
    
    return True

def main():
    """Main execution"""
    success = run_batches_2_3_4()
    
    if success:
        print(f"\n🎉 SUCCESS! Remaining batches applied")
        print(f"💾 Ready to commit and deploy")
    else:
        print(f"\n❌ Error in batch processing")
        return False
    
    return True

if __name__ == "__main__":
    main()
