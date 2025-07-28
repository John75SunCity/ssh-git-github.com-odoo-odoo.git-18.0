#!/usr/bin/env python3
"""
Comprehensive Model Reference Audit
Checks all Many2one and One2many fields to verify target models exist
"""

import os
import re
import sys

def extract_all_models():
    """Extract all model names defined in the module"""
    models = set()
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find all model names
            model_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            models.update(model_matches)
    
    return models

def extract_field_references():
    """Extract all Many2one and One2many field references"""
    references = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find source model name
            source_model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            if not source_model_match:
                continue
                
            source_model = source_model_match.group(1)
            
            # Find Many2one fields
            many2one_pattern = r"(\w+)\s*=\s*fields\.Many2one\s*\(\s*['\"]([^'\"]+)['\"]"
            many2one_matches = re.findall(many2one_pattern, content)
            
            for field_name, target_model in many2one_matches:
                references.append({
                    'source_file': filename,
                    'source_model': source_model,
                    'field_name': field_name,
                    'field_type': 'Many2one',
                    'target_model': target_model
                })
            
            # Find One2many fields
            one2many_pattern = r"(\w+)\s*=\s*fields\.One2many\s*\(\s*['\"]([^'\"]+)['\"]"
            one2many_matches = re.findall(one2many_pattern, content)
            
            for field_name, target_model in one2many_matches:
                references.append({
                    'source_file': filename,
                    'source_model': source_model,
                    'field_name': field_name,
                    'field_type': 'One2many',
                    'target_model': target_model
                })
    
    return references

def main():
    print("=== MODEL REFERENCE AUDIT ===")
    print()
    
    # Get all defined models
    defined_models = extract_all_models()
    print(f"Found {len(defined_models)} defined models in the module:")
    for model in sorted(defined_models):
        print(f"  ✓ {model}")
    print()
    
    # Get all field references
    references = extract_field_references()
    print(f"Found {len(references)} field references to audit:")
    print()
    
    # Standard Odoo models that we don't need to check
    standard_models = {
        'res.company', 'res.users', 'res.partner', 'ir.sequence', 'ir.attachment',
        'account.move', 'sale.order', 'stock.picking', 'stock.location',
        'product.product', 'product.template', 'mail.thread', 'mail.activity.mixin',
        'ir.ui.view', 'ir.logging', 'ir.module.module', 'survey.survey',
        'sign.request', 'hr.employee', 'res.country', 'res.country.state'
    }
    
    issues = []
    success_count = 0
    
    for ref in references:
        target_model = ref['target_model']
        
        if target_model in standard_models:
            print(f"✅ {ref['source_model']}.{ref['field_name']} -> {target_model} (standard)")
            success_count += 1
        elif target_model in defined_models:
            print(f"✅ {ref['source_model']}.{ref['field_name']} -> {target_model} (module)")
            success_count += 1
        else:
            print(f"❌ {ref['source_model']}.{ref['field_name']} -> {target_model} - MODEL NOT FOUND!")
            issues.append(ref)
    
    print()
    print(f"=== AUDIT SUMMARY ===")
    print(f"✅ Valid model references: {success_count}")
    print(f"❌ Missing target models: {len(issues)}")
    print()
    
    if issues:
        print("=== CRITICAL ISSUES TO FIX ===")
        for issue in issues:
            print(f"File: {issue['source_file']}")
            print(f"Model: {issue['source_model']}")
            print(f"Field: {issue['field_name']} ({issue['field_type']})")
            print(f"Missing target model: {issue['target_model']}")
            print("-" * 60)
        
        return 1  # Exit with error code
    else:
        print("🎉 All model references are valid!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
