#!/usr/bin/env python3
"""
Comprehensive Field Analysis for Records Management Module
Compares ALL field references in views against ALL model field definitions
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
import glob

def extract_view_fields():
    """Extract all field references from XML view files"""
    view_fields = defaultdict(set)
    
    # Find all XML view files
    xml_files = glob.glob('views/**/*.xml', recursive=True)
    xml_files.extend(glob.glob('data/**/*.xml', recursive=True))
    xml_files.extend(glob.glob('templates/**/*.xml', recursive=True))
    
    for xml_file in xml_files:
        try:
            # Parse XML to extract field references with model context
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            current_model = None
            
            # Find all elements with model attribute
            for elem in root.iter():
                if 'model' in elem.attrib:
                    current_model = elem.attrib['model']
                
                # Find field elements
                if elem.tag == 'field' and 'name' in elem.attrib:
                    field_name = elem.attrib['name']
                    if current_model and 'records.' in current_model:
                        view_fields[current_model].add(field_name)
                
                # Also check for field references in other contexts
                if elem.text and 'records.' in str(elem.text):
                    # Look for field references in expressions
                    field_refs = re.findall(r'(\w+)\.(\w+)', str(elem.text))
                    for model_ref, field_ref in field_refs:
                        if 'records' in model_ref:
                            view_fields[f'records.{model_ref}'].add(field_ref)
        
        except Exception as e:
            # Silently skip unparseable XML files and use regex fallback
            pass
    
    # Also use regex fallback for any missed references
    for xml_file in xml_files:
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find model context
                current_model = None
                lines = content.split('\n')
                
                for line in lines:
                    # Check for model definition in record, view, or action tags
                    model_match = re.search(r'model=["\']([^"\']*records[^"\']*)["\']', line)
                    if model_match:
                        current_model = model_match.group(1)
                    
                    # Only look for field elements (not view elements)
                    if '<field ' in line and 'name=' in line:
                        field_matches = re.findall(r'<field[^>]*name=["\']([^"\']*)["\'][^>]*(?:/>|>)', line)
                        for field_name in field_matches:
                            # Filter out obvious non-field names
                            if (current_model and 
                                not field_name.endswith('</field') and 
                                not field_name in ['form', 'tree', 'kanban', 'calendar', 'graph', 'pivot', 'search'] and
                                not '/' in field_name and
                                field_name.replace('_', '').replace('-', '').isalnum()):
                                view_fields[current_model].add(field_name)
                        
        except Exception as e:
            print(f"Error reading {xml_file}: {e}")
    
    return view_fields

def extract_model_fields():
    """Extract all field definitions from Python model files"""
    model_fields = {}
    
    # Find all Python model files
    py_files = glob.glob('models/**/*.py', recursive=True)
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find class definitions and model names
                class_matches = re.finditer(r'class\s+(\w+)\s*\([^)]*\):', content)
                
                for class_match in class_matches:
                    class_name = class_match.group(1)
                    class_start = class_match.start()
                    
                    # Find the _name attribute for this class
                    class_content = content[class_start:]
                    next_class = re.search(r'\nclass\s+\w+', class_content)
                    if next_class:
                        class_content = class_content[:next_class.start()]
                    
                    # Look for _name definition
                    name_match = re.search(r'_name\s*=\s*["\']([^"\']*)["\']', class_content)
                    if name_match:
                        model_name = name_match.group(1)
                        
                        # Extract field definitions
                        fields = set()
                        
                        # Find all field definitions
                        field_patterns = [
                            r'(\w+)\s*=\s*fields\.\w+\(',
                            r'(\w+)\s*=\s*fields\.\w+',
                        ]
                        
                        for pattern in field_patterns:
                            field_matches = re.findall(pattern, class_content, re.MULTILINE)
                            fields.update(field_matches)
                        
                        # Also look for computed fields and other field types
                        api_depends_matches = re.findall(r'def\s+(\w+)\s*\(', class_content)
                        for method_name in api_depends_matches:
                            if not method_name.startswith('_') or method_name.startswith('_compute_'):
                                if method_name.startswith('_compute_'):
                                    computed_field = method_name.replace('_compute_', '')
                                    fields.add(computed_field)
                        
                        if 'records.' in model_name:
                            model_fields[model_name] = fields
                            
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return model_fields

def find_missing_fields():
    """Compare view fields against model fields to find missing ones"""
    print("=== COMPREHENSIVE FIELD ANALYSIS ===\n")
    
    view_fields = extract_view_fields()
    model_fields = extract_model_fields()
    
    print("1. MODELS FOUND:")
    for model_name in sorted(model_fields.keys()):
        field_count = len(model_fields[model_name])
        print(f"   {model_name}: {field_count} fields")
    
    print("\n2. VIEW FIELD REFERENCES:")
    for model_name in sorted(view_fields.keys()):
        field_count = len(view_fields[model_name])
        print(f"   {model_name}: {field_count} field references")
    
    print("\n3. MISSING FIELD ANALYSIS:")
    total_missing = 0
    missing_by_model = {}
    
    for model_name in sorted(view_fields.keys()):
        if model_name in model_fields:
            view_field_set = view_fields[model_name]
            model_field_set = model_fields[model_name]
            
            missing_fields = view_field_set - model_field_set
            
            # Filter out standard Odoo fields that might be inherited
            standard_fields = {
                'id', 'create_date', 'create_uid', 'write_date', 'write_uid', 
                'display_name', '__last_update', 'access_url', 'access_token',
                'message_follower_ids', 'message_ids', 'activity_ids', 
                'activity_state', 'activity_exception_decoration', 'activity_type_icon',
                'message_attachment_count', 'message_has_error', 'message_has_error_counter',
                'message_has_sms_error', 'message_main_attachment_id', 'message_needaction',
                'message_needaction_counter', 'message_partner_ids', 'message_unread',
                'message_unread_counter', 'website_message_ids', 'website_id',
                'currency_id', 'company_id'
            }
            
            filtered_missing = missing_fields - standard_fields
            
            if filtered_missing:
                missing_by_model[model_name] = filtered_missing
                total_missing += len(filtered_missing)
                print(f"\n   {model_name}:")
                for field in sorted(filtered_missing):
                    print(f"     - {field}")
        else:
            print(f"\n   {model_name}: MODEL NOT FOUND!")
    
    print(f"\n4. SUMMARY:")
    print(f"   Total missing fields: {total_missing}")
    print(f"   Models with missing fields: {len(missing_by_model)}")
    
    if total_missing > 0:
        print(f"\n5. FIELD DEFINITIONS TO ADD:")
        for model_name, fields in missing_by_model.items():
            print(f"\n   # {model_name}")
            for field in sorted(fields):
                # Suggest field type based on name
                if field.endswith('_id'):
                    print(f"   {field} = fields.Many2one('model.name', string='{field.replace('_', ' ').title()}')")
                elif field.endswith('_ids'):
                    print(f"   {field} = fields.One2many('model.name', 'field_name', string='{field.replace('_', ' ').title()}')")
                elif field.endswith('_date'):
                    print(f"   {field} = fields.Date(string='{field.replace('_', ' ').title()}')")
                elif field.endswith('_count'):
                    print(f"   {field} = fields.Integer(string='{field.replace('_', ' ').title()}', compute='_compute_{field}')")
                elif 'amount' in field or 'cost' in field or 'price' in field:
                    print(f"   {field} = fields.Monetary(string='{field.replace('_', ' ').title()}')")
                elif field in ['active', 'required', 'verified', 'enabled']:
                    print(f"   {field} = fields.Boolean(string='{field.replace('_', ' ').title()}', default=True)")
                else:
                    print(f"   {field} = fields.Char(string='{field.replace('_', ' ').title()}')")
    
    return missing_by_model

if __name__ == "__main__":
    # Use the local records_management directory relative to script location
    import pathlib
    script_dir = pathlib.Path(__file__).parent.parent.parent / 'records_management'
    os.chdir(script_dir)
    missing_fields = find_missing_fields()
