#!/usr/bin/env python3
"""
Comprehensive One2many KeyError Fixer
Finds and fixes all One2many fields that reference non-existent inverse fields
"""

import os
import re
import sys

def find_all_one2many_fields():
    """Find all One2many fields in the models directory"""
    one2many_fields = []
    models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    
    for filename in os.listdir(models_dir):
        if not filename.endswith('.py'):
            continue
            
        filepath = os.path.join(models_dir, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find One2many field definitions
            pattern = r"(\w+)\s*=\s*fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(pattern, content)
            
            for field_name, model_name, inverse_field in matches:
                one2many_fields.append({
                    'file': filename,
                    'filepath': filepath,
                    'field_name': field_name,
                    'model_name': model_name,
                    'inverse_field': inverse_field,
                    'line_pattern': f"{field_name} = fields.One2many('{model_name}', '{inverse_field}'"
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

def fix_one2many_field(filepath, field_info, fix_type="many2many"):
    """Fix a problematic One2many field"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if fix_type == "many2many":
            # Convert to Many2many with relation parameter
            model_name = field_info['model_name']
            field_name = field_info['field_name']
            
            # Create a shorter relation name
            relation_name = f"{field_name}_rel"
            if len(relation_name) > 63:  # PostgreSQL limit
                relation_name = relation_name[:63]
                
            # Find the One2many definition and replace it
            old_pattern = rf"(\s*{field_name}\s*=\s*)fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]([^)]*)\)"
            
            def replacement(match):
                indent = match.group(1)
                model_ref = match.group(2)
                rest_params = match.group(4)
                
                # Remove the inverse field parameter and add relation
                rest_params = re.sub(r',\s*string\s*=', ', relation=\''+relation_name+'\', string=', rest_params)
                if 'string=' not in rest_params:
                    rest_params = f", relation='{relation_name}'{rest_params}"
                
                return f"{indent}fields.Many2many('{model_ref}'{rest_params})  # Fixed: was One2many with missing inverse field"
                
            new_content = re.sub(old_pattern, replacement, content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, f"Converted {field_name} to Many2many"
            else:
                return False, f"Could not find pattern for {field_name}"
                
        elif fix_type == "remove":
            # Comment out the problematic field
            pattern = rf"(\s*)({field_info['field_name']}\s*=\s*fields\.One2many[^)]*\))"
            
            def replacement(match):
                indent = match.group(1)
                field_def = match.group(2)
                return f"{indent}# DISABLED: {field_def}  # Missing inverse field '{field_info['inverse_field']}'"
                
            new_content = re.sub(pattern, replacement, content)
            
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                return True, f"Commented out {field_info['field_name']}"
            else:
                return False, f"Could not find field {field_info['field_name']}"
                
    except Exception as e:
        return False, f"Error fixing field: {e}"

def main():
    print("🔍 Finding all One2many fields...")
    one2many_fields = find_all_one2many_fields()
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
    
    print("\n🛠️  Fixing problematic fields...")
    
    fixed_count = 0
    failed_count = 0
    
    for field_info in problematic_fields:
        print(f"\nFixing {field_info['field_name']} in {field_info['file']}...")
        
        success, message = fix_one2many_field(field_info['filepath'], field_info, "many2many")
        
        if success:
            print(f"✅ {message}")
            fixed_count += 1
        else:
            print(f"❌ {message}")
            failed_count += 1
    
    print(f"\n📊 Summary:")
    print(f"✅ Fixed: {fixed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"🔍 Total checked: {len(one2many_fields)}")
    
    if fixed_count > 0:
        print(f"\n🚀 Fixed {fixed_count} One2many KeyError issues!")
        print("You can now try installing the module again.")
    
if __name__ == "__main__":
    main()
