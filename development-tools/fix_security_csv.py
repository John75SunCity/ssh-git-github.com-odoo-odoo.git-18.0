#!/usr/bin/env python3
"""
Script to identify and fix missing model references in security CSV file
"""

import os
import re

def get_model_names_from_python_files():
    """Extract model names from Python model files"""
    models_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models'
    model_names = set()
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find _name attributes
                name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                for name in name_matches:
                    model_names.add(name)
                    
            except Exception as e:
                print(f"Error reading {filename}: {e}")
    
    return model_names

def get_model_references_from_security():
    """Extract model references from security CSV file"""
    security_file = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management/security/ir.model.access.csv'
    model_refs = set()
    
    try:
        with open(security_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines[1:]:  # Skip header
            if line.strip():
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    model_ref = parts[2]  # model_id:id column
                    if model_ref.startswith('model_'):
                        model_name = model_ref[6:].replace('_', '.')  # Remove 'model_' prefix and replace _ with .
                        model_refs.add(model_name)
    
    except Exception as e:
        print(f"Error reading security file: {e}")
    
    return model_refs

def main():
    print("🔍 SECURITY CSV MODEL REFERENCE ANALYSIS")
    print("=" * 50)
    
    # Get actual models
    actual_models = get_model_names_from_python_files()
    print(f"\n📋 Found {len(actual_models)} actual models:")
    for model in sorted(actual_models):
        print(f"  ✅ {model}")
    
    # Get security references
    security_refs = get_model_references_from_security()
    print(f"\n🔐 Found {len(security_refs)} security references:")
    for ref in sorted(security_refs):
        print(f"  📝 {ref}")
    
    # Find missing models
    missing_models = security_refs - actual_models
    print(f"\n❌ Missing models ({len(missing_models)}):")
    for model in sorted(missing_models):
        print(f"  ❌ {model}")
    
    # Find extra models (not in security)
    extra_models = actual_models - security_refs
    print(f"\n➕ Models without security rules ({len(extra_models)}):")
    for model in sorted(extra_models):
        print(f"  ➕ {model}")
    
    return missing_models

if __name__ == '__main__':
    missing = main()
    print(f"\n🎯 SUMMARY: {len(missing)} missing model references need to be removed from security CSV")
