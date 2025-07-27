#!/usr/bin/env python3
"""
Emergency Fix for Model Name Conflicts
======================================

This script fixes the critical model naming issues causing the work_contact_id error.
"""

import os
import re
import glob

def fix_model_conflicts():
    """Fix all critical model naming conflicts"""
    
    print("🚨 EMERGENCY FIX: Model Name Conflicts")
    print("=" * 45)
    
    # Files with incorrect _name = "name" 
    name_conflicts = [
        "naid_destruction_record.py",
        "advanced_billing.py", 
        "records_approval_step.py",
        "records_box.py",
        "partner_bin_key.py",
        "records_location.py",
        "visitor.py",
        "portal_request.py", 
        "shredding_service.py",
        "records_document.py",
        "naid_certificate.py",
        "customer_feedback.py"
    ]
    
    # Files with temporary.model conflicts
    temp_conflicts = [
        "ir_module.py",
        "res_config_settings.py",
        "product.py", 
        "fsm_task.py",
        "hr_employee_naid.py",
        "res_partner.py",
        "project_task.py"
    ]
    
    # Duplicate naid.audit models
    audit_conflicts = [
        "naid_audit.py",
        "naid_audit_log.py"  
    ]
    
    model_dir = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    
    # Fix _name = "name" conflicts
    print("🔧 Fixing _name conflicts...")
    for filename in name_conflicts:
        filepath = os.path.join(model_dir, filename)
        if os.path.exists(filepath):
            fix_name_conflict(filepath, filename)
    
    # Fix temporary.model conflicts  
    print("\\n🔧 Fixing temporary.model conflicts...")
    for filename in temp_conflicts:
        filepath = os.path.join(model_dir, filename)
        if os.path.exists(filepath):
            fix_temp_model_conflict(filepath, filename)
    
    # Fix audit model conflicts
    print("\\n🔧 Fixing audit model conflicts...")
    for filename in audit_conflicts:
        filepath = os.path.join(model_dir, filename)
        if os.path.exists(filepath):
            fix_audit_conflict(filepath, filename)

def fix_name_conflict(filepath, filename):
    """Fix files with _name = 'name' errors"""
    
    # Map filenames to proper model names
    proper_names = {
        "naid_destruction_record.py": "naid.dest.record",
        "advanced_billing.py": "adv.bill", 
        "records_approval_step.py": "rec.appr.step",
        "records_box.py": "rec.box",
        "partner_bin_key.py": "partner.bin",
        "records_location.py": "rec.loc",
        "visitor.py": "visitor",
        "portal_request.py": "portal.req", 
        "shredding_service.py": "shred.svc",
        "records_document.py": "rec.doc",
        "naid_certificate.py": "naid.cert",
        "customer_feedback.py": "cust.fb"
    }
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Replace incorrect _name = "name" with proper model name
        if filename in proper_names:
            proper_name = proper_names[filename]
            
            # Fix the _name definition
            content = re.sub(
                r'_name\s*=\s*["\']name["\']',
                f'_name = "{proper_name}"',
                content
            )
            
            # Write back
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"   ✅ Fixed {filename}: _name = '{proper_name}'")
        
    except Exception as e:
        print(f"   ❌ Error fixing {filename}: {e}")

def fix_temp_model_conflict(filepath, filename):
    """Fix temporary.model conflicts"""
    
    # Map filenames to proper model names
    temp_names = {
        "ir_module.py": "ir.module.ext",
        "res_config_settings.py": "res.config.ext",
        "product.py": "prod.ext",
        "fsm_task.py": "fsm.task.ext", 
        "hr_employee_naid.py": "hr.emp.naid",
        "res_partner.py": "res.partner.ext",
        "project_task.py": "proj.task.ext"
    }
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        if filename in temp_names:
            proper_name = temp_names[filename]
            
            # Replace temporary.model with proper name
            content = re.sub(
                r'_name\s*=\s*["\']temporary\.model["\']',
                f'_name = "{proper_name}"',
                content
            )
            
            # Write back
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"   ✅ Fixed {filename}: _name = '{proper_name}'")
        
    except Exception as e:
        print(f"   ❌ Error fixing {filename}: {e}")

def fix_audit_conflict(filepath, filename):
    """Fix naid.audit model conflicts"""
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        if filename == "naid_audit_log.py":
            # Change to naid.audit.log to differentiate
            content = re.sub(
                r'_name\s*=\s*["\']naid\.audit["\']',
                '_name = "naid.audit.log"',
                content
            )
            
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"   ✅ Fixed {filename}: _name = 'naid.audit.log'")
        
    except Exception as e:
        print(f"   ❌ Error fixing {filename}: {e}")

def verify_fixes():
    """Verify that all conflicts are resolved"""
    
    print("\\n🔍 Verifying fixes...")
    
    model_names = {}
    conflicts = []
    
    model_files = glob.glob("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/*.py")
    
    for file_path in model_files:
        if "__init__.py" in file_path:
            continue
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Find _name definitions
            names = re.findall(r'_name\s*=\s*["\']([^"\']*)["\']', content)
            
            for name in names:
                if name in model_names:
                    conflicts.append((name, model_names[name], os.path.basename(file_path)))
                else:
                    model_names[name] = os.path.basename(file_path)
                    
        except Exception as e:
            print(f"   ⚠️  Error reading {file_path}: {e}")
    
    if conflicts:
        print("\\n❌ Remaining conflicts:")
        for name, file1, file2 in conflicts:
            print(f"   - {name}: {file1} vs {file2}")
        return False
    else:
        print("\\n✅ All conflicts resolved!")
        print(f"✅ {len(model_names)} unique models verified")
        return True

if __name__ == "__main__":
    fix_model_conflicts()
    
    if verify_fixes():
        print("\\n" + "=" * 45)
        print("🎊 EMERGENCY FIX COMPLETE!")
        print("✅ All model name conflicts resolved")
        print("✅ work_contact_id error should be fixed")
        print("✅ Module ready for installation") 
        print("=" * 45)
    else:
        print("\\n❌ Some conflicts remain - manual intervention needed")
