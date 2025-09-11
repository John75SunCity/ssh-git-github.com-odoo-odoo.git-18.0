#!/usr/bin/env python3
"""
Properly verify model definitions with correct regex
"""

import os
import re
import glob

def verify_model_definitions():
    """Verify that models have proper _name and _rec_name definitions"""
    
    print("🔍 Verifying model definitions with corrected regex...")
    
    models_dir = "records_management/models/"
    all_good = True
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Use more precise regex - _name must be followed by space or =, not preceded by _rec
            name_matches = re.findall(r'(?<!_rec)_name\s*=\s*["\'][^"\']+["\']', content)
            rec_name_matches = re.findall(r'_rec_name\s*=\s*["\'][^"\']+["\']', content)
            
            if len(name_matches) > 1:
                print(f"   ❌ Multiple _name definitions in {file_path}: {name_matches}")
                all_good = False
            elif len(name_matches) == 1:
                print(f"   ✅ {os.path.basename(file_path)}: {name_matches[0]}")
                if rec_name_matches:
                    print(f"      └─ {rec_name_matches[0]}")
            elif len(name_matches) == 0:
                print(f"   ⚠️  {os.path.basename(file_path)}: No _name definition found")
            
        except Exception as e:
            print(f"   ❌ Error checking {file_path}: {e}")
            all_good = False
    
    return all_good

def check_for_work_contact_references():
    """Check for any references to work_contact_id that might be causing the error"""
    
    print("\n🔍 Checking for work_contact_id references...")
    
    models_dir = "records_management/models/"
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            if 'work_contact_id' in content:
                print(f"   🎯 Found work_contact_id in {file_path}")
                # Show the lines containing work_contact_id
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if 'work_contact_id' in line:
                        print(f"      Line {i+1}: {line.strip()}")
                        
        except Exception as e:
            print(f"   ❌ Error checking {file_path}: {e}")

if __name__ == "__main__":
    print("🚨 MODEL VERIFICATION: Corrected Analysis")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    # Verify model definitions with corrected regex
    success = verify_model_definitions()
    
    # Check for the specific error we're trying to fix
    check_for_work_contact_references()
    
    if success:
        print("\n✅ All model definitions are correct!")
        print("   No duplicate _name issues found.")
    else:
        print("\n❌ Model definition issues found - see output above")
