#!/usr/bin/env python3
"""
Fix the incorrectly replaced _name fields back to _rec_name
"""

import os
import re
import glob

def fix_incorrect_name_replacements():
    """Fix files where _name was incorrectly replaced instead of _rec_name"""
    
    print("🔧 Fixing incorrectly replaced _name fields...")
    
    models_dir = "records_management/models/"
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for patterns where we have both a proper _name and an incorrect _name = "name"
            lines = content.split('\n')
            fixed_lines = []
            found_proper_name = False
            
            for line in lines:
                # Check if this line has a proper _name definition
                if re.match(r'\s*_name\s*=\s*["\'][^"\']+["\']', line) and '"name"' not in line and "'name'" not in line:
                    found_proper_name = True
                    fixed_lines.append(line)
                # If we find _name = "name" and we already have a proper _name, convert it to _rec_name
                elif re.match(r'\s*_name\s*=\s*["\']name["\']', line) and found_proper_name:
                    fixed_lines.append(line.replace('_name =', '_rec_name ='))
                    print(f"   ✅ Fixed {file_path}: converted _name = 'name' to _rec_name = 'name'")
                else:
                    fixed_lines.append(line)
            
            # Write back the fixed content
            with open(file_path, 'w') as f:
                f.write('\n'.join(fixed_lines))
                
        except Exception as e:
            print(f"   ❌ Error fixing {file_path}: {e}")

def verify_model_definitions():
    """Verify that each model has exactly one _name and one _rec_name"""
    
    print("\n🔍 Verifying model definitions...")
    
    models_dir = "records_management/models/"
    all_good = True
    
    for file_path in glob.glob(os.path.join(models_dir, "*.py")):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Count _name definitions
            name_matches = re.findall(r'_name\s*=\s*["\'][^"\']+["\']', content)
            rec_name_matches = re.findall(r'_rec_name\s*=\s*["\'][^"\']+["\']', content)
            
            if len(name_matches) > 1:
                print(f"   ❌ Multiple _name definitions in {file_path}: {name_matches}")
                all_good = False
            elif len(name_matches) == 1:
                if len(rec_name_matches) == 1:
                    print(f"   ✅ {file_path}: Correct - 1 _name, 1 _rec_name")
                elif len(rec_name_matches) == 0:
                    print(f"   ⚠️  {file_path}: Missing _rec_name (this is usually OK)")
                else:
                    print(f"   ❌ {file_path}: Multiple _rec_name definitions: {rec_name_matches}")
                    all_good = False
            
        except Exception as e:
            print(f"   ❌ Error checking {file_path}: {e}")
            all_good = False
    
    return all_good

if __name__ == "__main__":
    print("🚨 EMERGENCY FIX: Incorrect _name Replacements")
    print("=" * 50)
    
    # Change to the correct directory
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    # Fix the incorrect replacements
    fix_incorrect_name_replacements()
    
    # Verify all model definitions
    success = verify_model_definitions()
    
    if success:
        print("\n✅ All model definitions are now correct!")
        print("   Ready to test module installation.")
    else:
        print("\n❌ Some issues remain - manual intervention needed")
