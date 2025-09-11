#!/usr/bin/env python3
"""
Comprehensive One2many Relationship Audit
Checks all One2many fields and verifies their inverse fields exist
"""

import os
import re
import sys

def extract_one2many_relationships():
    """Extract all One2many relationships from Python models"""
    relationships = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find model name
            model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            if not model_match:
                continue
                
            model_name = model_match.group(1)
            
            # Find One2many fields
            one2many_pattern = r"(\w+)\s*=\s*fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(one2many_pattern, content)
            
            for field_name, target_model, inverse_field in matches:
                relationships.append({
                    'source_file': filename,
                    'source_model': model_name,
                    'field_name': field_name,
                    'target_model': target_model,
                    'inverse_field': inverse_field,
                    'line_context': f"{field_name} -> {target_model}.{inverse_field}"
                })
    
    return relationships

def check_inverse_field_exists(target_model, inverse_field):
    """Check if the inverse field exists in the target model"""
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if this file contains the target model
            model_match = re.search(r"_name\s*=\s*['\"]" + re.escape(target_model) + r"['\"]", content)
            if not model_match:
                continue
                
            # Check if inverse field exists
            field_pattern = r"\b" + re.escape(inverse_field) + r"\s*=\s*fields\."
            if re.search(field_pattern, content):
                return True, filename
                
    return False, None

def main():
    print("=== ONE2MANY RELATIONSHIP AUDIT ===")
    print()
    
    relationships = extract_one2many_relationships()
    print(f"Found {len(relationships)} One2many relationships to audit:")
    print()
    
    issues = []
    success_count = 0
    
    for rel in relationships:
        exists, target_file = check_inverse_field_exists(rel['target_model'], rel['inverse_field'])
        
        if exists:
            print(f"✅ {rel['line_context']} (in {target_file})")
            success_count += 1
        else:
            print(f"❌ {rel['line_context']} - MISSING INVERSE FIELD!")
            issues.append(rel)
    
    print()
    print(f"=== AUDIT SUMMARY ===")
    print(f"✅ Valid relationships: {success_count}")
    print(f"❌ Missing inverse fields: {len(issues)}")
    print()
    
    if issues:
        print("=== CRITICAL ISSUES TO FIX ===")
        for issue in issues:
            print(f"File: {issue['source_file']}")
            print(f"Model: {issue['source_model']}")
            print(f"Field: {issue['field_name']}")
            print(f"Target: {issue['target_model']}")
            print(f"Missing inverse field: {issue['inverse_field']}")
            print(f"Fix: Add '{issue['inverse_field']} = fields.Many2one('{issue['source_model']}')' to {issue['target_model']} model")
            print("-" * 60)
        
        return 1  # Exit with error code
    else:
        print("🎉 All One2many relationships have valid inverse fields!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
