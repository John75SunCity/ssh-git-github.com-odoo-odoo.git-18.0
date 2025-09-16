#!/usr/bin/env python3
"""
Comprehensive field validation for retention policy views
Validates that all field references in views exist in the corresponding models
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path

def extract_model_fields(py_file_path):
    """Extract all field definitions from a Python model file"""
    fields = {}
    try:
        with open(py_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all field definitions: field_name = fields.FieldType(...)
        field_pattern = r'^\s*(\w+)\s*=\s*fields\.(\w+)\s*\('
        matches = re.finditer(field_pattern, content, re.MULTILINE)
        
        for match in matches:
            field_name = match.group(1)
            field_type = match.group(2)
            fields[field_name] = field_type
            
        # Also add standard Odoo fields that are always available
        odoo_standard_fields = {
            'id': 'Integer',
            'create_date': 'Datetime', 
            'create_uid': 'Many2one',
            'write_date': 'Datetime',
            'write_uid': 'Many2one',
            'display_name': 'Char',
            '__last_update': 'Datetime'
        }
        fields.update(odoo_standard_fields)
        
    except Exception as e:
        print(f"Error reading model file {py_file_path}: {e}")
        
    return fields

def extract_view_field_references(xml_file_path):
    """Extract all field references from XML view files"""
    field_refs = []
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Find all <field name="..."> elements
        for field_elem in root.findall('.//field[@name]'):
            field_name = field_elem.get('name')
            if field_name:
                field_refs.append(field_name)
                
        # Also check for field references in domains, contexts, etc.
        xpath_contexts = [
            './/filter[@domain]',
            './/record[@domain]', 
            './/field[@domain]',
            './/button[@context]'
        ]
        
        for xpath in xpath_contexts:
            for elem in root.findall(xpath):
                domain_or_context = elem.get('domain') or elem.get('context') or ''
                # Extract field names from domain/context strings
                field_matches = re.findall(r"'(\w+)'", domain_or_context)
                field_refs.extend(field_matches)
                
    except Exception as e:
        print(f"Error reading view file {xml_file_path}: {e}")
        
    return list(set(field_refs))  # Remove duplicates

def validate_retention_policy_fields():
    """Validate field references in retention policy views"""
    base_path = Path("records_management")
    
    # Model file paths
    model_files = {
        'records.retention.policy': base_path / "models" / "records_retention_policy.py",
        'records.retention.policy.version': base_path / "models" / "records_retention_policy_version.py"
    }
    
    # View file paths  
    view_files = [
        base_path / "views" / "records_retention_policy_views.xml",
        base_path / "views" / "records_retention_policy_version_views.xml"
    ]
    
    print("=== RETENTION POLICY FIELD VALIDATION ===\n")
    
    # Extract model fields
    model_fields = {}
    for model_name, model_file in model_files.items():
        if model_file.exists():
            fields = extract_model_fields(model_file)
            model_fields[model_name] = fields
            print(f"✅ Model {model_name}: Found {len(fields)} fields")
        else:
            print(f"❌ Model file not found: {model_file}")
    
    print()
    
    # Validate each view file
    all_issues = []
    
    for view_file in view_files:
        if not view_file.exists():
            print(f"❌ View file not found: {view_file}")
            continue
            
        print(f"🔍 Validating: {view_file.name}")
        field_refs = extract_view_field_references(view_file)
        print(f"   Found {len(field_refs)} field references")
        
        # Determine which model this view is for based on filename
        if "policy_version" in str(view_file):
            target_model = 'records.retention.policy.version'
        else:
            target_model = 'records.retention.policy'
            
        if target_model not in model_fields:
            print(f"   ❌ No model fields available for validation")
            continue
            
        # Check each field reference
        valid_fields = model_fields[target_model]
        issues = []
        
        for field_ref in field_refs:
            if field_ref not in valid_fields:
                issues.append(f"   ❌ Field '{field_ref}' not found in model {target_model}")
            else:
                print(f"   ✅ Field '{field_ref}' -> {valid_fields[field_ref]}")
                
        if issues:
            print(f"   Found {len(issues)} field validation issues:")
            for issue in issues:
                print(issue)
                all_issues.append(f"{view_file.name}: {issue}")
        else:
            print("   ✅ All field references are valid!")
            
        print()
    
    # Summary
    print("=== VALIDATION SUMMARY ===")
    if all_issues:
        print(f"❌ Found {len(all_issues)} field validation issues:")
        for issue in all_issues:
            print(f"   {issue}")
            
        print("\n🔧 RECOMMENDED ACTIONS:")
        print("1. Remove invalid field references from views")
        print("2. Replace with existing model fields")
        print("3. Add missing fields to models if needed")
        print("4. Use standard Odoo fields (create_uid, write_uid) for user tracking")
        
    else:
        print("✅ All field references are valid!")
        print("🚀 Views are ready for deployment!")

if __name__ == "__main__":
    validate_retention_policy_fields()
