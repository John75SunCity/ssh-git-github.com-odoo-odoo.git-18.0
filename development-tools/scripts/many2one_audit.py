#!/usr/bin/env python3
"""
Comprehensive Many2one Relationship Audit for Records Management Module
Checks for missing target models referenced by Many2one fields
"""

import os
import re
import glob
from collections import defaultdict

def get_all_model_names():
    """Get all model names defined in the records_management module"""
    models = set()
    
    # Standard Odoo models that should exist
    odoo_models = {
        'res.company', 'res.users', 'res.partner', 'res.groups',
        'account.move', 'account.payment.term', 'product.product',
        'res.currency', 'mail.message', 'mail.activity', 'mail.followers',
        'ir.ui.view', 'ir.attachment', 'fleet.vehicle'
    }
    models.update(odoo_models)
    
    model_files = glob.glob('records_management/models/*.py')
    for file_path in model_files:
        if '__init__' in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find _name definitions
            name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            models.update(name_matches)
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return models

def find_many2one_references():
    """Find all Many2one field references"""
    many2one_refs = []
    
    model_files = glob.glob('records_management/models/*.py')
    for file_path in model_files:
        if '__init__' in file_path:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                # Find Many2one field definitions
                many2one_match = re.search(r"fields\.Many2one\s*\(\s*['\"]([^'\"]+)['\"]", line)
                if many2one_match:
                    target_model = many2one_match.group(1)
                    many2one_refs.append({
                        'file': file_path,
                        'line': line_num,
                        'target_model': target_model,
                        'line_content': line.strip()
                    })
                    
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return many2one_refs

def audit_many2one_relationships():
    """Audit Many2one relationships for missing targets"""
    print("=== MANY2ONE RELATIONSHIP AUDIT ===\n")
    
    # Get all available models
    available_models = get_all_model_names()
    print(f"Found {len(available_models)} available models")
    
    # Get all Many2one references
    many2one_refs = find_many2one_references()
    print(f"Found {len(many2one_refs)} Many2one field references\n")
    
    # Group by target model
    refs_by_model = defaultdict(list)
    for ref in many2one_refs:
        refs_by_model[ref['target_model']].append(ref)
    
    # Check for missing models
    missing_models = []
    existing_models = []
    
    for target_model, refs in refs_by_model.items():
        if target_model not in available_models:
            missing_models.append((target_model, refs))
        else:
            existing_models.append((target_model, refs))
    
    # Report results
    print("=== MISSING TARGET MODELS ===")
    if missing_models:
        for model_name, refs in missing_models:
            print(f"\n❌ MISSING MODEL: '{model_name}'")
            print(f"   Referenced by {len(refs)} field(s):")
            for ref in refs:
                file_short = ref['file'].replace('records_management/models/', '')
                print(f"   - {file_short}:{ref['line']} -> {ref['line_content']}")
    else:
        print("✅ No missing target models found!")
    
    print(f"\n=== EXISTING TARGET MODELS ===")
    print(f"✅ {len(existing_models)} target models exist and are valid")
    
    # Show custom models being referenced
    custom_models = []
    for model_name, refs in existing_models:
        if not model_name.startswith(('res.', 'account.', 'product.', 'mail.', 'ir.', 'fleet.')):
            custom_models.append((model_name, len(refs)))
    
    if custom_models:
        print(f"\n=== CUSTOM MODELS BEING REFERENCED ===")
        for model_name, ref_count in sorted(custom_models, key=lambda x: x[1], reverse=True):
            print(f"✅ {model_name} ({ref_count} references)")
    
    return missing_models, existing_models

if __name__ == "__main__":
    missing, existing = audit_many2one_relationships()
    
    if missing:
        print(f"\n🚨 SUMMARY: {len(missing)} missing target models need to be created")
        print("These models should be created to resolve Many2one relationship errors:")
        for model_name, refs in missing:
            print(f"  - {model_name}")
    else:
        print(f"\n🎉 SUMMARY: All Many2one relationships are valid!")
