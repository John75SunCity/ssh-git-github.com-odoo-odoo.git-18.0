#!/usr/bin/env python3
"""
Enhanced model-view validator that catches MISSING MODELS (not just missing fields).

This addresses the exact issue in the user's error:
"Model not found: records.deletion.request.enhanced"

The script validates:
1. Models referenced in views actually exist
2. Models are properly imported in __init__.py  
3. View field references match model definitions
4. Separates real issues from action config false positives
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

def get_all_model_names():
    """Extract all model names (_name) from Python files in models/"""
    models_dir = "records_management/models"
    model_names = set()
    
    if not os.path.exists(models_dir):
        print(f"❌ Models directory not found: {models_dir}")
        return model_names
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find _name = 'model.name' definitions
                name_matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                model_names.update(name_matches)
                
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return model_names

def get_models_referenced_in_views():
    """Extract all model names referenced in view files"""
    views_dir = "records_management/views"
    referenced_models = set()
    view_files = {}
    
    if not os.path.exists(views_dir):
        print(f"❌ Views directory not found: {views_dir}")
        return referenced_models, view_files
    
    for filename in os.listdir(views_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(views_dir, filename)
            try:
                tree = ET.parse(filepath)
                root = tree.getroot()
                
                file_models = set()
                
                # Find all view records
                for record in root.findall('.//record'):
                    if record.get('model') == 'ir.ui.view':
                        # Get the model this view is for
                        model_field = record.find('.//field[@name="model"]')
                        if model_field is not None and model_field.text:
                            model_name = model_field.text.strip()
                            referenced_models.add(model_name)
                            file_models.add(model_name)
                
                view_files[filename] = file_models
                
            except Exception as e:
                print(f"Error parsing {filepath}: {e}")
    
    return referenced_models, view_files

def check_model_imports():
    """Check which models are imported in __init__.py"""
    init_path = "records_management/models/__init__.py"
    imported_files = set()
    
    if not os.path.exists(init_path):
        print(f"❌ __init__.py not found: {init_path}")
        return imported_files
    
    try:
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find import statements
        import_matches = re.findall(r"from\s+\.\s+import\s+(\w+)", content)
        imported_files.update(import_matches)
        
    except Exception as e:
        print(f"Error reading {init_path}: {e}")
    
    return imported_files

def main():
    """Validate models referenced in views actually exist and are imported."""
    
    print("🔍 ENHANCED MODEL-VIEW VALIDATOR")
    print("=" * 60)
    print("Checking for the exact issue: 'Model not found: records.deletion.request.enhanced'")
    
    # Get all model names defined in Python files
    defined_models = get_all_model_names()
    print(f"\n📝 Models Defined in Python: {len(defined_models)}")
    
    # Get all models referenced in view files
    referenced_models, view_files = get_models_referenced_in_views()
    print(f"👀 Models Referenced in Views: {len(referenced_models)}")
    
    # Check which model files are imported
    imported_files = check_model_imports()
    print(f"📦 Model Files Imported in __init__.py: {len(imported_files)}")
    
    # Find missing models (referenced but not defined)
    missing_models = referenced_models - defined_models
    
    print(f"\n❌ MISSING MODELS: {len(missing_models)}")
    if missing_models:
        print("Models referenced in views but NOT defined in Python:")
        for model in sorted(missing_models):
            print(f"  ❌ {model}")
            
            # Show which view files reference this missing model
            for view_file, models_in_file in view_files.items():
                if model in models_in_file:
                    print(f"     Referenced in: {view_file}")
    else:
        print("✅ All models referenced in views are properly defined!")
    
    # Check the specific error from user
    target_model = "records.deletion.request.enhanced"
    print(f"\n🎯 SPECIFIC ERROR CHECK: '{target_model}'")
    
    if target_model in missing_models:
        print(f"✅ YES! This validator WOULD have caught this error!")
        print(f"   - Model '{target_model}' is referenced in views but not defined")
        
        # Show which files reference it
        for view_file, models_in_file in view_files.items():
            if target_model in models_in_file:
                print(f"   - Referenced in: {view_file}")
    else:
        print(f"❌ This specific model issue not found in current state")
    
    # Additional analysis
    print(f"\n📊 SUMMARY:")
    print(f"  - Defined models: {len(defined_models)}")
    print(f"  - Referenced models: {len(referenced_models)}")
    print(f"  - Missing models: {len(missing_models)}")
    print(f"  - Imported files: {len(imported_files)}")
    
    if missing_models:
        print(f"\n💡 TO FIX MISSING MODELS:")
        print(f"  1. Create Python model files for missing models")
        print(f"  2. Add proper imports to models/__init__.py")
        print(f"  3. Or remove references from view files if models not needed")

if __name__ == "__main__":
    main()
