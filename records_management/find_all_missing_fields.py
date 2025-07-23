#!/usr/bin/env python3
"""
COMPREHENSIVE FIELD ANALYSIS SCRIPT
Finds ALL missing fields in ALL models across the entire Records Management module
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

def extract_fields_from_python_file(file_path):
    """Extract all field definitions from a Python model file"""
    fields = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Match field definitions: field_name = fields.FieldType(...)
        field_pattern = r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*fields\.[A-Za-z_][A-Za-z0-9_]*\('
        for line in content.split('\n'):
            match = re.match(field_pattern, line)
            if match:
                field_name = match.group(1)
                # Skip private fields and methods
                if not field_name.startswith('_') and field_name not in ['fields']:
                    fields.add(field_name)
                    
        # Also extract inherited fields from _inherit models
        inherit_pattern = r"_inherit\s*=\s*['\"]([^'\"]+)['\"]"
        inherit_matches = re.findall(inherit_pattern, content)
        
        return fields, inherit_matches
        
    except Exception as e:
        print(f"Error reading Python file {file_path}: {e}")
        return set(), []

def extract_model_name_from_python_file(file_path):
    """Extract the model name from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for _name definition
        name_pattern = r"_name\s*=\s*['\"]([^'\"]+)['\"]"
        name_match = re.search(name_pattern, content)
        if name_match:
            return name_match.group(1)
            
        # Look for class name and convert to model name
        class_pattern = r'class\s+([A-Za-z][A-Za-z0-9_]*)\(models\.Model\)'
        class_match = re.search(class_pattern, content)
        if class_match:
            class_name = class_match.group(1)
            # Convert CamelCase to dot.notation
            model_name = re.sub(r'([a-z0-9])([A-Z])', r'\1.\2', class_name).lower()
            return model_name
            
    except Exception as e:
        print(f"Error reading Python file {file_path}: {e}")
        
    return None

def extract_fields_from_xml_file(file_path):
    """Extract all field references from an XML view file"""
    field_references = defaultdict(set)
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Find all field elements
        for field_elem in root.findall('.//field'):
            field_name = field_elem.get('name')
            if field_name:
                # Try to determine the model context
                model_context = None
                
                # Look for model in parent elements
                parent = field_elem
                while parent is not None:
                    if parent.tag == 'record' and parent.get('model'):
                        if 'view' in parent.get('model', ''):
                            # This is a view definition, look for the model it refers to
                            for child in parent:
                                if child.tag == 'field' and child.get('name') == 'model':
                                    model_context = child.text
                                    break
                        break
                    elif parent.tag in ['tree', 'form', 'kanban', 'search', 'calendar', 'graph', 'pivot']:
                        # Look for model in arch context or record
                        record_parent = parent
                        while record_parent is not None:
                            if record_parent.tag == 'record':
                                for child in record_parent:
                                    if child.tag == 'field' and child.get('name') == 'model':
                                        model_context = child.text
                                        break
                                break
                            record_parent = record_parent.getparent() if hasattr(record_parent, 'getparent') else None
                        break
                    parent = parent.getparent() if hasattr(parent, 'getparent') else None
                
                # Also extract model from file context by examining other records
                if not model_context:
                    for record in root.findall('.//record'):
                        for field in record.findall('.//field[@name="model"]'):
                            if field.text and '.' in field.text:
                                model_context = field.text
                                break
                        if model_context:
                            break
                
                if model_context:
                    field_references[model_context].add(field_name)
                else:
                    # Add to unknown context for manual review
                    field_references['__unknown__'].add(field_name)
                    
    except Exception as e:
        print(f"Error parsing XML file {file_path}: {e}")
        
    return field_references

def main():
    """Main analysis function"""
    base_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    # Dictionary to store all model fields
    model_fields = {}
    
    # Dictionary to store all field references from views
    view_field_references = defaultdict(set)
    
    print("🔍 COMPREHENSIVE FIELD ANALYSIS STARTING...")
    print("=" * 60)
    
    # Step 1: Extract all fields from Python model files
    print("\n📄 STEP 1: Analyzing Python Model Files...")
    models_path = os.path.join(base_path, 'models')
    if os.path.exists(models_path):
        for filename in os.listdir(models_path):
            if filename.endswith('.py') and not filename.startswith('__'):
                file_path = os.path.join(models_path, filename)
                model_name = extract_model_name_from_python_file(file_path)
                fields, inherits = extract_fields_from_python_file(file_path)
                
                if model_name and fields:
                    model_fields[model_name] = fields
                    print(f"  ✓ {model_name}: {len(fields)} fields")
                elif fields:
                    print(f"  ? {filename}: {len(fields)} fields (unknown model name)")
    
    # Step 2: Extract all field references from XML view files
    print(f"\n📋 STEP 2: Analyzing XML View Files...")
    views_path = os.path.join(base_path, 'views')
    if os.path.exists(views_path):
        for filename in os.listdir(views_path):
            if filename.endswith('.xml'):
                file_path = os.path.join(views_path, filename)
                file_references = extract_fields_from_xml_file(file_path)
                
                for model, fields in file_references.items():
                    view_field_references[model].update(fields)
                    print(f"  ✓ {filename}: {len(fields)} field references for {model}")
    
    # Step 3: Compare and find missing fields
    print(f"\n🔎 STEP 3: Comparing Fields and Finding Missing...")
    missing_fields = defaultdict(set)
    
    for model, referenced_fields in view_field_references.items():
        if model == '__unknown__':
            continue
            
        if model in model_fields:
            defined_fields = model_fields[model]
            missing = referenced_fields - defined_fields
            if missing:
                missing_fields[model] = missing
        else:
            # Model not found in our analysis
            missing_fields[model] = referenced_fields
    
    # Step 4: Report Results
    print(f"\n📊 STEP 4: RESULTS SUMMARY")
    print("=" * 60)
    
    if missing_fields:
        print(f"❌ MISSING FIELDS FOUND: {sum(len(fields) for fields in missing_fields.values())} total")
        print()
        
        for model, fields in missing_fields.items():
            print(f"🚨 Model: {model}")
            for field in sorted(fields):
                print(f"   - {field}")
            print()
    else:
        print("✅ NO MISSING FIELDS FOUND!")
    
    # Step 5: Detailed model analysis
    print(f"\n📋 STEP 5: DETAILED MODEL ANALYSIS")
    print("=" * 60)
    
    print(f"Models analyzed: {len(model_fields)}")
    for model, fields in sorted(model_fields.items()):
        print(f"  {model}: {len(fields)} fields")
    
    print(f"\nView references analyzed: {len(view_field_references)}")
    for model, fields in sorted(view_field_references.items()):
        if model != '__unknown__':
            print(f"  {model}: {len(fields)} field references")
    
    if '__unknown__' in view_field_references:
        unknown_fields = view_field_references['__unknown__']
        print(f"\n⚠️  Unknown context fields: {len(unknown_fields)}")
        for field in sorted(unknown_fields):
            print(f"   - {field}")

if __name__ == "__main__":
    main()
