#!/usr/bin/env python3
"""
Remove duplicate _name = "name" lines that were incorrectly added
"""

import os
import re
import glob

def remove_duplicate_name_lines():
    """Remove lines with _name = "name" that are duplicates"""
    
    print("🔧 Removing duplicate _name = 'name' lines...")
    
    # Files that have the duplicate issue
    problematic_files = [
        'records_management/models/naid_destruction_record.py',
        'records_management/models/advanced_billing.py', 
        'records_management/models/records_approval_step.py',
        'records_management/models/records_box.py',
        'records_management/models/partner_bin_key.py',
        'records_management/models/records_location.py',
        'records_management/models/visitor.py',
        'records_management/models/portal_request.py',
        'records_management/models/shredding_service.py',
        'records_management/models/records_document.py',
        'records_management/models/naid_certificate.py',
        'records_management/models/customer_feedback.py'
    ]
    
    for file_path in problematic_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                
                # Remove lines that are just _name = "name" or _name = 'name'
                filtered_lines = []
                for line in lines:
                    # Skip lines that are exactly _name = "name" or _name = 'name'
                    if re.match(r'\s*_name\s*=\s*["\']name["\']\s*$', line.strip()):
                        print(f"   ✅ Removed duplicate _name = 'name' from {file_path}")
                    else:
                        filtered_lines.append(line)
                
                # Write back the cleaned content
                with open(file_path, 'w') as f:
                    f.writelines(filtered_lines)
                    
            except Exception as e:
                print(f"   ❌ Error fixing {file_path}: {e}")
        else:
            print(f"   ⚠️  File not found: {file_path}")

def fix_shredding_service_log():
    """Fix the shredding_service_log.py file that has _name = activity_description"""
    
    file_path = 'records_management/models/shredding_service_log.py'
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Replace _name = "activity_description" with _rec_name = "activity_description"
            if '_name = "activity_description"' in content:
                content = content.replace('_name = "activity_description"', '_rec_name = "activity_description"')
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                print(f"   ✅ Fixed {file_path}: _name = 'activity_description' -> _rec_name = 'activity_description'")
                
        except Exception as e:
            print(f"   ❌ Error fixing {file_path}: {e}")

def verify_final_state():
    """Final verification that all models are clean"""
    
    print("\n🔍 Final verification...")
    
    models_dir = "records_management/models/"
    issues_found = 0
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Count _name definitions
            name_matches = re.findall(r'_name\s*=\s*["\'][^"\']+["\']', content)
            
            if len(name_matches) > 1:
                print(f"   ❌ Multiple _name definitions in {file_path}: {name_matches}")
                issues_found += 1
            elif len(name_matches) == 1:
                # Check if it's a problematic _name = "name"
                if name_matches[0] in ['_name = "name"', "_name = 'name'"]:
                    print(f"   ❌ Found _name = 'name' in {file_path}")
                    issues_found += 1
            
        except Exception as e:
            print(f"   ❌ Error checking {file_path}: {e}")
            issues_found += 1
    
    return issues_found == 0

if __name__ == "__main__":
    print("🚨 EMERGENCY FIX: Remove Duplicate _name Lines")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    # Remove duplicate _name = "name" lines
    remove_duplicate_name_lines()
    
    # Fix the shredding service log
    fix_shredding_service_log()
    
    # Final verification
    success = verify_final_state()
    
    if success:
        print("\n✅ All duplicate _name entries removed successfully!")
        print("   Models are now clean and ready for installation.")
    else:
        print("\n❌ Some issues remain - check output above")
