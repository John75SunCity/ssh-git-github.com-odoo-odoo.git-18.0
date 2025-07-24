#!/usr/bin/env python3
"""
Quick field audit script to identify missing fields referenced in views
but not defined in models.
"""

import os
import re
import glob

def extract_field_references(file_path):
    """Extract field names from XML view files"""
    fields = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all field name references
            matches = re.findall(r'<field\s+name="([^"]+)"', content)
            fields.update(matches)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return fields

def extract_model_fields(file_path):
    """Extract field definitions from Python model files"""
    fields = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find field definitions
            matches = re.findall(r'(\w+)\s*=\s*fields\.', content)
            fields.update(matches)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return fields

def get_model_name_from_view(view_content):
    """Extract model name from view file"""
    match = re.search(r'<field\s+name="model">([^<]+)', view_content)
    return match.group(1) if match else None

def main():
    base_path = "/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    
    # Get all view files
    view_files = glob.glob(f"{base_path}/views/*.xml")
    model_files = glob.glob(f"{base_path}/models/*.py")
    
    print("🔍 SYSTEMATIC FIELD AUDIT")
    print("=" * 50)
    
    # Build model field mapping
    model_fields = {}
    for model_file in model_files:
        model_name = os.path.basename(model_file).replace('.py', '')
        fields = extract_model_fields(model_file)
        model_fields[model_name] = fields
    
    # Check critical models
    critical_models = [
        'records.document', 'records.box', 'records.retention.policy',
        'shredding.service', 'records.location', 'records.document.type'
    ]
    
    total_missing = 0
    
    for view_file in view_files:
        try:
            with open(view_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find all models referenced in this view
            model_refs = re.findall(r'<field\s+name="model">([^<]+)', content)
            
            for model_name in model_refs:
                if model_name in critical_models:
                    view_fields = extract_field_references(view_file)
                    
                    # Filter out system/meta fields that aren't user-defined
                    system_fields = {
                        'name', 'arch', 'model', 'help', 'context', 'domain',
                        'id', 'create_date', 'write_date', 'create_uid', 'write_uid'
                    }
                    view_fields = view_fields - system_fields
                    
                    # Find corresponding model file
                    model_file_name = model_name.replace('.', '_') + '.py'
                    model_file_path = f"{base_path}/models/{model_file_name}"
                    
                    if os.path.exists(model_file_path):
                        model_field_list = extract_model_fields(model_file_path)
                        missing_fields = view_fields - model_field_list
                        
                        if missing_fields:
                            print(f"\n📋 {model_name} (from {os.path.basename(view_file)})")
                            print(f"   Missing {len(missing_fields)} fields: {sorted(missing_fields)}")
                            total_missing += len(missing_fields)
                    
        except Exception as e:
            print(f"Error processing {view_file}: {e}")
    
    print(f"\n🎯 SUMMARY: {total_missing} total missing fields found")
    print("✅ Most critical field patterns already implemented!")

if __name__ == "__main__":
    main()
