#!/usr/bin/env python3
"""
Comprehensive Field Name Mismatch Detector
Finds field references in views that don't match model field names
"""

import os
import re
import xml.etree.ElementTree as ET

def extract_model_fields():
    """Extract all field names from Python models"""
    model_fields = {}
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
            
            # Find all field definitions
            field_pattern = r"(\w+)\s*=\s*fields\.\w+"
            fields = re.findall(field_pattern, content)
            
            model_fields[model_name] = set(fields)
    
    return model_fields

def check_view_field_references():
    """Check field references in XML views against model definitions"""
    print("=== FIELD NAME MISMATCH DETECTOR ===")
    print()
    
    model_fields = extract_model_fields()
    views_dir = "records_management/views"
    
    mismatches = []
    
    for filename in os.listdir(views_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(views_dir, filename)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find field references and their models
                # Look for patterns like <field name="field_name" in records.model context
                field_refs = re.findall(r'<field\s+name="([^"]+)"', content)
                
                # Try to determine model from view context
                model_matches = re.findall(r'res_model[\'"]?\s*[:=]\s*[\'"]([^\'\"]+)[\'"]', content)
                model_matches.extend(re.findall(r'view\.model[\'"]?\s*[:=]\s*[\'"]([^\'\"]+)[\'"]', content))
                
                if model_matches:
                    primary_model = model_matches[0]
                    
                    if primary_model in model_fields:
                        available_fields = model_fields[primary_model]
                        
                        for field_ref in field_refs:
                            if field_ref not in available_fields:
                                # Check if it might be a related field or computed field
                                if '.' not in field_ref and '_id' not in field_ref:
                                    mismatches.append({
                                        'file': filename,
                                        'model': primary_model,
                                        'field': field_ref,
                                        'available_fields': sorted(available_fields)
                                    })
                
            except Exception as e:
                print(f"⚠️  Error processing {filename}: {e}")
    
    if mismatches:
        print("❌ POTENTIAL FIELD MISMATCHES FOUND:")
        print()
        for mismatch in mismatches[:10]:  # Limit output
            print(f"File: {mismatch['file']}")
            print(f"Model: {mismatch['model']}")
            print(f"Missing field: {mismatch['field']}")
            
            # Suggest similar field names
            field_name = mismatch['field']
            suggestions = [f for f in mismatch['available_fields'] if field_name in f or f in field_name]
            if suggestions:
                print(f"Possible matches: {suggestions}")
            print("-" * 50)
    else:
        print("✅ No obvious field mismatches detected!")
    
    print()
    print(f"Checked {len(model_fields)} models with field definitions")

if __name__ == "__main__":
    check_view_field_references()
