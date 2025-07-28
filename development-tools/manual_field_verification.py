#!/usr/bin/env python3
"""
Manual verification of the supposedly missing fields
"""

import os
import re

def check_if_field_exists(model_name, field_name):
    """Check if a field exists in a specific model"""
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if this file contains the target model
            if f"_name = '{model_name}'" in content or f'_name = "{model_name}"' in content:
                # Check if field exists
                field_pattern = rf'\b{field_name}\s*=\s*fields\.'
                if re.search(field_pattern, content):
                    return True, filename
                    
    return False, None

def main():
    print("=== MANUAL FIELD VERIFICATION ===")
    print()
    
    # Check the supposedly missing fields
    problem_fields = [
        ('records.container', 'bale_date'),
        ('records.container', 'gross_weight'),
        ('records.container', 'service_type'),
        ('records.container', 'state'),
        ('records.location', 'state'),
    ]
    
    for model_name, field_name in problem_fields:
        exists, filename = check_if_field_exists(model_name, field_name)
        
        if exists:
            print(f"✅ {model_name}.{field_name} EXISTS in {filename}")
        else:
            print(f"❌ {model_name}.{field_name} MISSING")
    
    print()
    
    # Check if these are actually bale-related fields
    print("=== CHECKING FOR BALE MODELS ===")
    bale_models = []
    models_dir = "records_management/models"
    
    for filename in os.listdir(models_dir):
        if 'bale' in filename and filename.endswith('.py'):
            filepath = os.path.join(models_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find model name
            model_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            if model_match:
                model_name = model_match.group(1)
                bale_models.append((model_name, filename))
                print(f"📦 {model_name} in {filename}")
    
    print()
    print("=== CHECKING BALE MODELS FOR THESE FIELDS ===")
    
    for model_name, filename in bale_models:
        print(f"\n--- {model_name} ---")
        for field in ['bale_date', 'gross_weight', 'service_type', 'state']:
            exists, _ = check_if_field_exists(model_name, field)
            status = "✅" if exists else "❌"
            print(f"  {status} {field}")

if __name__ == "__main__":
    main()
