#!/usr/bin/env python3
"""
Enhanced One2many KeyError Fixer - Handles multi-line definitions
"""

import os
import re
import sys

def find_multiline_one2many_fields():
    """Find One2many fields including multi-line definitions"""
    one2many_fields = []
    models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    
    for filename in os.listdir(models_dir):
        if not filename.endswith('.py'):
            continue
            
        filepath = os.path.join(models_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Enhanced pattern for multi-line One2many fields
            pattern = r"(\w+)\s*=\s*fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"],?\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            
            for field_name, model_name, inverse_field in matches:
                one2many_fields.append({
                    'file': filename,
                    'filepath': filepath,
                    'field_name': field_name.strip(),
                    'model_name': model_name.strip(),
                    'inverse_field': inverse_field.strip(),
                })
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return one2many_fields

def find_model_files():
    """Create a mapping of model names to their file paths"""
    model_files = {}
    models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    
    for filename in os.listdir(models_dir):
        if not filename.endswith('.py'):
            continue
            
        filepath = os.path.join(models_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find model definitions
            pattern = r"_name\s*=\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(pattern, content)
            
            for model_name in matches:
                model_files[model_name] = filepath
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return model_files

def check_inverse_field_exists(model_name, inverse_field, model_files):
    """Check if the inverse field exists in the target model"""
    if model_name not in model_files:
        return False, f"Model '{model_name}' not found"
        
    try:
        with open(model_files[model_name], 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if the inverse field exists
        field_pattern = rf"\b{inverse_field}\s*="
        if re.search(field_pattern, content):
            return True, "Field exists"
        else:
            return False, f"Field '{inverse_field}' not found in model '{model_name}'"
            
    except Exception as e:
        return False, f"Error checking model file: {e}"

def main():
    print("🔍 Enhanced One2many field search (including multi-line)...")
    one2many_fields = find_multiline_one2many_fields()
    print(f"Found {len(one2many_fields)} One2many fields")
    
    print("\n🗂️  Mapping model files...")
    model_files = find_model_files()
    print(f"Found {len(model_files)} models")
    
    print("\n🔧 Checking for problematic One2many relationships...")
    
    problematic_fields = []
    
    for field_info in one2many_fields:
        exists, reason = check_inverse_field_exists(
            field_info['model_name'], 
            field_info['inverse_field'], 
            model_files
        )
        
        if not exists:
            problematic_fields.append(field_info)
            print(f"❌ {field_info['file']}:{field_info['field_name']} -> {field_info['model_name']}.{field_info['inverse_field']} - {reason}")
        else:
            print(f"✅ {field_info['file']}:{field_info['field_name']} -> {field_info['model_name']}.{field_info['inverse_field']} - OK")
    
    if not problematic_fields:
        print("\n🎉 No problematic One2many fields found!")
        return
        
    print(f"\n⚠️  Found {len(problematic_fields)} problematic One2many fields")
    print("\nProblematic fields that need manual fixing:")
    for field_info in problematic_fields:
        print(f"  📄 {field_info['file']} - {field_info['field_name']} -> {field_info['model_name']}.{field_info['inverse_field']}")

if __name__ == "__main__":
    main()
