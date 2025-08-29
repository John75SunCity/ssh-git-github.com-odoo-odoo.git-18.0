#!/usr/bin/env python3
"""
Fix model references in XML files after removing model_external_ids.xml
"""
import re
import os
import glob

def find_all_models():
    """Find all model names from Python files."""
    models = set()
    python_files = glob.glob('records_management/models/*.py')
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find _name = 'model.name' patterns
                matches = re.findall(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                models.update(matches)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return models

def update_xml_file(file_path, valid_models):
    """Update XML file to use correct model references."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        updated = False
        
        # Find all ref="model_..." patterns
        pattern = r'ref="(model_[a-z_]+)"'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # Convert model_some_name to some.name
            model_name = match.replace('model_', '').replace('_', '.')
            
            if model_name in valid_models:
                # Replace with correct external ID
                old_ref = f'ref="{match}"'
                new_ref = f'ref="records_management.{match}"'
                content = content.replace(old_ref, new_ref)
                updated = True
                print(f"  Updated {match} -> records_management.{match}")
            else:
                print(f"  WARNING: {file_path} references non-existent model: {model_name}")
        
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {file_path}")
        
    except Exception as e:
        print(f"Error updating {file_path}: {e}")

def main():
    print("Finding all valid models...")
    valid_models = find_all_models()
    print(f"Found {len(valid_models)} models:")
    for model in sorted(valid_models):
        print(f"  - {model}")
    print()
    
    print("Updating XML files...")
    xml_files = glob.glob('records_management/**/*.xml', recursive=True)
    
    for xml_file in xml_files:
        # Skip the model_external_ids.xml file itself
        if 'model_external_ids.xml' in xml_file:
            continue
        
        print(f"Checking {xml_file}...")
        update_xml_file(xml_file, valid_models)

if __name__ == '__main__':
    main()
