#!/usr/bin/env python3
"""
Task ID Relationship Verification Script
Verifies all One2many relationships that use 'task_id' as inverse field
"""
import os
import re
import glob

def verify_task_id_relationships():
    """Verify all task_id inverse relationships are properly configured"""
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0"
    models_path = os.path.join(base_path, "records_management", "models")
    
    print("🔍 VERIFYING TASK_ID RELATIONSHIPS...")
    print("=" * 60)
    
    # Find all One2many fields that use task_id as inverse
    one2many_task_refs = []
    model_fields = {}
    
    # Scan all model files
    for py_file in glob.glob(os.path.join(models_path, "*.py")):
        if py_file.endswith("__init__.py"):
            continue
            
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        filename = os.path.basename(py_file)
        
        # Find model names in this file
        model_matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        
        # Find all fields in this file  
        field_matches = re.findall(r'(\w+)\s*=\s*fields\.(\w+)', content)
        for field_name, field_type in field_matches:
            for model_name in model_matches:
                if model_name not in model_fields:
                    model_fields[model_name] = {}
                model_fields[model_name][field_name] = field_type
        
        # Find One2many fields with task_id inverse
        one2many_pattern = r'(\w+)\s*=\s*fields\.One2many\s*\(\s*["\']([^"\']+)["\']\s*,\s*["\']task_id["\']\s*(?:,\s*[^)]+)?\s*\)'
        matches = re.finditer(one2many_pattern, content)
        
        for match in matches:
            field_name = match.group(1)
            comodel = match.group(2) 
            one2many_task_refs.append({
                'file': filename,
                'field_name': field_name,
                'comodel': comodel,
                'line_content': match.group(0)
            })
    
    print(f"📋 Found {len(one2many_task_refs)} One2many fields using 'task_id' as inverse:")
    print()
    
    all_valid = True
    
    for ref in one2many_task_refs:
        print(f"🔗 {ref['file']}: {ref['field_name']}")
        print(f"   Comodel: {ref['comodel']}")
        print(f"   Inverse: task_id")
        
        # Check if comodel has task_id field
        if ref['comodel'] in model_fields:
            if 'task_id' in model_fields[ref['comodel']]:
                field_type = model_fields[ref['comodel']]['task_id']
                print(f"   ✅ VALID: {ref['comodel']} has task_id field ({field_type})")
            else:
                print(f"   ❌ MISSING: {ref['comodel']} lacks task_id field!")
                all_valid = False
        else:
            print(f"   ⚠️  UNKNOWN: {ref['comodel']} model not found in scanned files")
            # Could be external Odoo core model
            if ref['comodel'].startswith(('project.', 'mail.', 'res.')):
                print(f"   ℹ️  External model - assuming task_id field exists")
            else:
                all_valid = False
        print()
    
    print("=" * 60)
    if all_valid:
        print("🎉 SUCCESS: All task_id relationships appear to be properly configured!")
        print("✅ No missing inverse fields detected")
    else:
        print("⚠️  ISSUES: Some task_id relationships may still have problems")
        print("❌ Manual verification recommended")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total models scanned: {len(model_fields)}")
    print(f"   Models with task_id field: {sum(1 for fields in model_fields.values() if 'task_id' in fields)}")
    print(f"   One2many → task_id relationships: {len(one2many_task_refs)}")
    
    return all_valid, one2many_task_refs, model_fields

if __name__ == "__main__":
    verify_task_id_relationships()
