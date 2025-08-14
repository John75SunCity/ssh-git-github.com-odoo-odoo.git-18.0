#!/usr/bin/env python3
"""
Quick Critical Field Checker
Identifies models that are genuinely missing critical fields
"""

import os
import re
import glob

def check_model_file(filepath):
    """Check if a model file has critical fields"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Skip if this is not a regular model (TransientModel, Abstract, etc.)
        if 'TransientModel' in content or '_abstract = True' in content:
            return None
            
        # Skip inheritance models that don't define new models
        if '_inherit =' in content and '_name =' not in content:
            return None
            
        # Get model name
        model_name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if not model_name_match:
            return None
            
        model_name = model_name_match.group(1)
        
        # Check for critical fields
        missing_fields = []
        
        # Check for name field
        if not re.search(r"name\s*=\s*fields\.", content):
            missing_fields.append('name')
            
        # Check for active field  
        if not re.search(r"active\s*=\s*fields\.", content):
            missing_fields.append('active')
            
        # Check for company_id field
        if not re.search(r"company_id\s*=\s*fields\.", content):
            missing_fields.append('company_id')
            
        # Check for state field (not always required but common)
        if not re.search(r"state\s*=\s*fields\.", content):
            missing_fields.append('state')
            
        if missing_fields:
            return {
                'file': os.path.basename(filepath),
                'model': model_name,
                'missing': missing_fields
            }
            
        return None
        
    except Exception as e:
        print(f"Error checking {filepath}: {e}")
        return None

def main():
    """Main function"""
    print("🔍 Checking for models missing critical fields...\n")
    
    # Find all model files
    model_files = glob.glob('records_management/models/*.py')
    
    models_needing_fields = []
    
    for filepath in sorted(model_files):
        if '__init__.py' in filepath:
            continue
            
        result = check_model_file(filepath)
        if result:
            models_needing_fields.append(result)
    
    if not models_needing_fields:
        print("✅ All models have critical fields!")
        return
        
    print(f"🚨 Found {len(models_needing_fields)} models missing critical fields:\n")
    
    for model_info in models_needing_fields:
        print(f"📁 {model_info['file']}")
        print(f"   Model: {model_info['model']}")
        print(f"   Missing: {', '.join(model_info['missing'])}")
        print()

if __name__ == '__main__':
    main()
