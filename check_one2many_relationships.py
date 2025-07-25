#!/usr/bin/env python3

import os
import re
import ast

def find_one2many_fields():
    """Find all One2many fields and check if their inverse fields exist"""
    model_dir = "records_management/models"
    issues = []
    
    # Get all Python model files
    model_files = []
    for file in os.listdir(model_dir):
        if file.endswith('.py') and file != '__init__.py':
            model_files.append(os.path.join(model_dir, file))
    
    # Find all One2many fields
    one2many_fields = []
    
    for model_file in model_files:
        try:
            with open(model_file, 'r') as f:
                content = f.read()
                
            # Find One2many field definitions
            one2many_pattern = r"(\w+)\s*=\s*fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(one2many_pattern, content)
            
            for field_name, comodel, inverse_field in matches:
                one2many_fields.append({
                    'file': model_file,
                    'field_name': field_name,
                    'comodel': comodel,
                    'inverse_field': inverse_field
                })
        except Exception as e:
            print(f"Error reading {model_file}: {e}")
    
    print(f"Found {len(one2many_fields)} One2many fields:")
    print("=" * 80)
    
    # Check each One2many field
    for field_info in one2many_fields:
        print(f"\nChecking: {field_info['field_name']} -> {field_info['comodel']}.{field_info['inverse_field']}")
        
        # Find the target model file
        comodel_name = field_info['comodel']
        expected_filename = comodel_name.replace('.', '_') + '.py'
        target_file = os.path.join(model_dir, expected_filename)
        
        if not os.path.exists(target_file):
            print(f"  ❌ TARGET MODEL FILE NOT FOUND: {target_file}")
            issues.append(f"Missing model file: {target_file}")
            continue
            
        # Check if inverse field exists in target model
        try:
            with open(target_file, 'r') as f:
                target_content = f.read()
                
            inverse_field_pattern = rf"{field_info['inverse_field']}\s*=\s*fields\."
            if re.search(inverse_field_pattern, target_content):
                print(f"  ✅ Inverse field '{field_info['inverse_field']}' found in {target_file}")
            else:
                print(f"  ❌ MISSING INVERSE FIELD: {field_info['inverse_field']} in {target_file}")
                issues.append(f"Missing inverse field: {field_info['inverse_field']} in {target_file}")
                
        except Exception as e:
            print(f"  ❌ Error checking {target_file}: {e}")
            issues.append(f"Error checking {target_file}: {e}")
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: Found {len(issues)} issues")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")
    
    return issues

if __name__ == "__main__":
    find_one2many_fields()
