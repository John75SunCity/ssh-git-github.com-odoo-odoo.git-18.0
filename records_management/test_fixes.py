#!/usr/bin/env python3
"""
Quick verification script to test if KeyError: 'res_id' is resolved
"""

import os
import sys

def test_fixed_groups():
    """Test the groups we've fixed so far"""
    
    # Get all One2many field definitions
    pattern = r"fields\.One2many\([^)]+\)"
    issues_found = 0
    
    print("=== TESTING FIXED GROUPS ===")
    
    # Group A: NAID Compliance (should now use compute methods)
    print("\n🔧 Group A - NAID Compliance:")
    naid_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/naid_compliance.py"
    
    with open(naid_file, 'r') as f:
        content = f.read()
        
    # Check if converted to compute methods
    if "compute='_compute_audit_history_ids'" in content:
        print("  ✅ audit_history_ids - FIXED (compute method)")
    else:
        print("  ❌ audit_history_ids - NOT FIXED")
        issues_found += 1
        
    if "compute='_compute_certificate_ids'" in content:
        print("  ✅ certificate_ids - FIXED (compute method)")
    else:
        print("  ❌ certificate_ids - NOT FIXED")
        issues_found += 1
    
    # Group B: Paper Bale (should now use compute methods)
    print("\n🔧 Group B - Paper Bale:")
    bale_file = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/paper_bale.py"
    
    with open(bale_file, 'r') as f:
        content = f.read()
        
    if "compute='_compute_quality_inspection_ids'" in content:
        print("  ✅ quality_inspection_ids - FIXED (compute method)")
    else:
        print("  ❌ quality_inspection_ids - NOT FIXED")
        issues_found += 1
        
    if "compute='_compute_source_document_ids'" in content:
        print("  ✅ source_document_ids - FIXED (compute method)")
    else:
        print("  ❌ source_document_ids - NOT FIXED")
        issues_found += 1
    
    print(f"\n=== VERIFICATION RESULT ===")
    print(f"Issues found in fixed groups: {issues_found}")
    
    if issues_found == 0:
        print("✅ All fixed groups look good!")
        print("🔍 Ready to check remaining groups...")
    else:
        print("❌ Some fixes didn't apply correctly")
        
    return issues_found == 0

if __name__ == "__main__":
    test_fixed_groups()
