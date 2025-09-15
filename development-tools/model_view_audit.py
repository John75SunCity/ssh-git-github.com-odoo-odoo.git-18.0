#!/usr/bin/env python3
"""
Model-View Field Audit Script for Records Management Module
===========================================================

This script audits the synchronization between model fields and view field references.
It identifies:
1. Fields referenced in views that don't exist in models
2. Models referenced in views that don't exist
3. Common field naming patterns that are mismatched

Usage: python3 development-tools/model_view_audit.py
"""

import os
import re
import glob
import ast
from collections import defaultdict


def extract_model_fields(model_file):
    """Extract field definitions from a Python model file."""
    try:
        with open(model_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find field definitions using regex
        field_pattern = r'(\w+)\s*=\s*fields\.\w+'
        fields = re.findall(field_pattern, content)
        
        # Also check for _name definition
        name_pattern = r'_name\s*=\s*[\'"]([^\'"]+)[\'"]'
        name_match = re.search(name_pattern, content)
        model_name = name_match.group(1) if name_match else None
        
        return model_name, fields
    except Exception as e:
        print(f"Error parsing {model_file}: {e}")
        return None, []


def extract_view_fields(view_file):
    """Extract field references from an XML view file."""
    try:
        with open(view_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find field name references
        field_pattern = r'<field\s+name="([^"]+)"'
        fields = re.findall(field_pattern, content)
        
        # Find model references
        model_pattern = r'<field\s+name="model">([^<]+)</field>'
        models = re.findall(model_pattern, content)
        
        return models, fields
    except Exception as e:
        print(f"Error parsing {view_file}: {e}")
        return [], []


def main():
    print("🔍 Records Management - Model-View Field Audit")
    print("=" * 60)
    
    # Change to records_management directory
    os.chdir('records_management')
    
    # Collect all model field definitions
    model_fields = {}
    model_files = glob.glob('models/*.py')
    
    print(f"📁 Found {len(model_files)} model files")
    
    for model_file in model_files:
        model_name, fields = extract_model_fields(model_file)
        if model_name and fields:
            model_fields[model_name] = fields
            print(f"  ✅ {model_name}: {len(fields)} fields")
    
    print(f"\n📊 Total models processed: {len(model_fields)}")
    print(f"📋 Total unique model names: {len(set(model_fields.keys()))}")
    
    # Collect all view field references
    view_files = glob.glob('views/*.xml')
    print(f"\n📁 Found {len(view_files)} view files")
    
    issues = defaultdict(list)
    
    for view_file in view_files:
        models, fields = extract_view_fields(view_file)
        
        for model in models:
            if model not in model_fields:
                issues['missing_models'].append((view_file, model))
            else:
                # Check if fields exist in the model
                model_field_list = model_fields[model]
                for field in fields:
                    if field not in model_field_list and field not in ['arch', 'model', 'name', 'inherit_id']:
                        issues['missing_fields'].append((view_file, model, field))
    
    # Report issues
    print("\n🚨 AUDIT RESULTS")
    print("=" * 40)
    
    if issues['missing_models']:
        print(f"\n❌ Missing Models ({len(issues['missing_models'])} issues):")
        for view_file, model in issues['missing_models']:
            print(f"  📄 {view_file} → {model}")
    
    if issues['missing_fields']:
        print(f"\n⚠️  Missing Fields ({len(issues['missing_fields'])} issues):")
        grouped_by_model = defaultdict(list)
        for view_file, model, field in issues['missing_fields']:
            grouped_by_model[model].append((view_file, field))
        
        for model, field_issues in grouped_by_model.items():
            print(f"\n  🏷️  Model: {model}")
            for view_file, field in field_issues:
                print(f"    📄 {view_file} → missing field '{field}'")
    
    if not issues['missing_models'] and not issues['missing_fields']:
        print("✅ No model-view synchronization issues found!")
    
    print(f"\n📈 Summary:")
    print(f"  • Models: {len(model_fields)}")
    print(f"  • Views: {len(view_files)}")
    print(f"  • Missing Models: {len(issues['missing_models'])}")
    print(f"  • Missing Fields: {len(issues['missing_fields'])}")


if __name__ == '__main__':
    main()
