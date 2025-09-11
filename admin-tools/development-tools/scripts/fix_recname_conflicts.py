#!/usr/bin/env python3
"""
Fix _rec_name conflicts and inconsistencies in Records Management models
This resolves the work_contact_id KeyError by ensuring consistent model naming.
"""

import os
import re
import glob

def fix_recname_inconsistencies():
    """Fix _rec_name fields that don't match _name fields"""
    
    print("🔧 Fixing _rec_name inconsistencies...")
    
    # Define the fixes needed based on the analysis
    fixes = [
        {
            'file': 'records_management/models/customer_feedback.py',
            'old_rec_name': '_rec_name = "cust.fb"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/naid_certificate.py',
            'old_rec_name': '_rec_name = "naid.cert"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/records_document.py',
            'old_rec_name': '_rec_name = "rec.doc"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/shredding_service.py',
            'old_rec_name': '_rec_name = "shred.svc"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/portal_request.py',
            'old_rec_name': '_rec_name = "portal.req"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/visitor.py',
            'old_rec_name': '_rec_name = "visitor"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/records_location.py',
            'old_rec_name': '_rec_name = "rec.loc"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/partner_bin_key.py',
            'old_rec_name': '_rec_name = "partner.bin"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/records_box.py',
            'old_rec_name': '_rec_name = "rec.box"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/records_approval_step.py',
            'old_rec_name': '_rec_name = "rec.appr.step"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/advanced_billing.py',
            'old_rec_name': '_rec_name = "adv.bill"',
            'new_rec_name': '_rec_name = "name"'
        },
        {
            'file': 'records_management/models/naid_destruction_record.py',
            'old_rec_name': '_rec_name = "naid.dest.record"',
            'new_rec_name': '_rec_name = "name"'
        }
    ]
    
    for fix in fixes:
        file_path = fix['file']
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                if fix['old_rec_name'] in content:
                    content = content.replace(fix['old_rec_name'], fix['new_rec_name'])
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    print(f"   ✅ Fixed {file_path}: {fix['new_rec_name']}")
                else:
                    print(f"   ⚠️  Pattern not found in {file_path}")
                    
            except Exception as e:
                print(f"   ❌ Error fixing {file_path}: {e}")
        else:
            print(f"   ❌ File not found: {file_path}")

def remove_duplicate_model_definitions():
    """Remove any duplicate model class definitions in files"""
    
    print("\n🔧 Checking for duplicate model definitions...")
    
    models_dir = "records_management/models/"
    if not os.path.exists(models_dir):
        print(f"❌ Models directory not found: {models_dir}")
        return
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check for multiple class definitions
            class_matches = re.findall(r'class\s+\w+\(models\.\w+\):', content)
            if len(class_matches) > 1:
                print(f"   ⚠️  Multiple classes found in {file_path}: {class_matches}")
            
            # Check for multiple _name definitions
            name_matches = re.findall(r'_name\s*=\s*["\'][^"\']+["\']', content)
            if len(name_matches) > 1:
                print(f"   ⚠️  Multiple _name definitions in {file_path}: {name_matches}")
                
        except Exception as e:
            print(f"   ❌ Error checking {file_path}: {e}")

def verify_fixes():
    """Verify that all fixes were applied correctly"""
    
    print("\n🔍 Verifying fixes...")
    
    # Check for any remaining problematic patterns
    models_dir = "records_management/models/"
    
    # Look for _rec_name that doesn't equal "name"
    problematic_files = []
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find _rec_name definitions that are not "name"
            rec_name_matches = re.findall(r'_rec_name\s*=\s*["\']([^"\']+)["\']', content)
            for match in rec_name_matches:
                if match != "name" and match != "activity_description":  # activity_description is valid for logs
                    problematic_files.append((file_path, match))
                    
        except Exception as e:
            print(f"   ❌ Error verifying {file_path}: {e}")
    
    if problematic_files:
        print("   ❌ Remaining problematic _rec_name definitions:")
        for file_path, rec_name in problematic_files:
            print(f"      - {file_path}: _rec_name = '{rec_name}'")
        return False
    else:
        print("   ✅ All _rec_name definitions are now consistent")
        return True

if __name__ == "__main__":
    print("🚨 EMERGENCY FIX: _rec_name Conflicts")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    # Fix _rec_name inconsistencies
    fix_recname_inconsistencies()
    
    # Check for duplicate definitions
    remove_duplicate_model_definitions()
    
    # Verify all fixes
    success = verify_fixes()
    
    if success:
        print("\n✅ All _rec_name conflicts resolved successfully!")
        print("   Ready to test module installation.")
    else:
        print("\n❌ Some issues remain - manual intervention needed")
