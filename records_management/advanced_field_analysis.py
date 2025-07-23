#!/usr/bin/env python3
"""
Advanced Field Analysis - Find missing fields by matching view fields to specific models
"""

import os
import re
import glob
from collections import defaultdict

def extract_model_fields():
    """Extract all field definitions from Python model files"""
    model_fields = {}
    
    py_files = glob.glob('models/**/*.py', recursive=True)
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find class definitions
                class_matches = re.finditer(r'class\s+(\w+)\s*\([^)]*\):(.*?)(?=\nclass|\n\n\n|\Z)', content, re.DOTALL)
                
                for class_match in class_matches:
                    class_name = class_match.group(1)
                    class_content = class_match.group(2)
                    
                    # Find _name definition
                    name_match = re.search(r'_name\s*=\s*["\']([^"\']*)["\']', class_content)
                    if name_match:
                        model_name = name_match.group(1)
                        
                        if 'records.' in model_name:
                            # Extract field definitions
                            fields = set()
                            
                            # Field definitions
                            field_patterns = [
                                r'(\w+)\s*=\s*fields\.\w+\(',
                                r'(\w+)\s*=\s*fields\.\w+',
                            ]
                            
                            for pattern in field_patterns:
                                field_matches = re.findall(pattern, class_content, re.MULTILINE)
                                fields.update(field_matches)
                            
                            # Computed fields
                            compute_matches = re.findall(r'def\s+_compute_(\w+)', class_content)
                            fields.update(compute_matches)
                            
                            # Add standard Odoo fields
                            standard_fields = {
                                'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
                                'display_name', '__last_update', 'access_url', 'access_token',
                                'message_follower_ids', 'message_ids', 'activity_ids',
                                'activity_state', 'activity_exception_decoration',
                                'message_attachment_count', 'message_has_error',
                                'message_has_error_counter', 'message_has_sms_error',
                                'message_main_attachment_id', 'message_needaction',
                                'message_needaction_counter', 'message_partner_ids',
                                'message_unread', 'message_unread_counter',
                                'website_message_ids'
                            }
                            fields.update(standard_fields)
                            
                            model_fields[model_name] = fields
                            
        except Exception as e:
            print(f"Error processing {py_file}: {e}")
    
    return model_fields

def extract_view_fields_by_model():
    """Extract field references grouped by model from view files"""
    view_fields = defaultdict(set)
    
    xml_files = glob.glob('views/**/*.xml', recursive=True)
    xml_files.extend(glob.glob('data/**/*.xml', recursive=True))
    
    for xml_file in xml_files:
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Look for record definitions with model attribute
                record_pattern = r'<record[^>]*model="([^"]*records[^"]*)"[^>]*>(.*?)</record>'
                record_matches = re.finditer(record_pattern, content, re.DOTALL)
                
                for record_match in record_matches:
                    model_name = record_match.group(1)
                    record_content = record_match.group(2)
                    
                    # Extract field references from this record
                    field_matches = re.findall(r'<field[^>]*name="([^"]+)"', record_content)
                    for field_name in field_matches:
                        if (field_name.replace('_', '').isalnum() and 
                            field_name not in ['form', 'tree', 'kanban', 'calendar', 'graph', 'pivot', 'search']):
                            view_fields[model_name].add(field_name)
                
                # Also look for xpath and other references that might indicate model context
                lines = content.split('\n')
                current_model = None
                
                for line in lines:
                    # Track model context
                    model_match = re.search(r'model="([^"]*records[^"]*)"', line)
                    if model_match:
                        current_model = model_match.group(1)
                    
                    # Extract field references when we have model context
                    if current_model and '<field ' in line:
                        field_matches = re.findall(r'<field[^>]*name="([^"]+)"', line)
                        for field_name in field_matches:
                            if (field_name.replace('_', '').isalnum() and 
                                field_name not in ['form', 'tree', 'kanban', 'calendar', 'graph', 'pivot', 'search']):
                                view_fields[current_model].add(field_name)
                
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
    
    return view_fields

def analyze_missing_fields():
    """Main analysis function"""
    print("=== COMPREHENSIVE MISSING FIELD ANALYSIS ===\n")
    
    model_fields = extract_model_fields()
    view_fields = extract_view_fields_by_model()
    
    print("MODELS WITH FIELDS:")
    for model_name in sorted(model_fields.keys()):
        print(f"  {model_name}: {len(model_fields[model_name])} fields")
    
    print(f"\nVIEW REFERENCES BY MODEL:")
    for model_name in sorted(view_fields.keys()):
        print(f"  {model_name}: {len(view_fields[model_name])} field references")
    
    print(f"\nMISSING FIELD ANALYSIS:")
    
    total_missing = 0
    missing_by_model = {}
    
    for model_name in sorted(view_fields.keys()):
        if model_name in model_fields:
            view_field_set = view_fields[model_name]
            model_field_set = model_fields[model_name]
            
            missing_fields = view_field_set - model_field_set
            
            if missing_fields:
                missing_by_model[model_name] = missing_fields
                total_missing += len(missing_fields)
                
                print(f"\n  {model_name}:")
                for field in sorted(missing_fields):
                    print(f"    ❌ {field}")
        else:
            print(f"\n  {model_name}: ⚠️  MODEL DEFINITION NOT FOUND")
    
    if total_missing == 0:
        print("\n✅ NO MISSING FIELDS FOUND! All field references have corresponding model definitions.")
    else:
        print(f"\n📊 SUMMARY:")
        print(f"  Total missing fields: {total_missing}")
        print(f"  Models affected: {len(missing_by_model)}")
        
        print(f"\n🔧 FIELD DEFINITIONS TO ADD:")
        for model_name, fields in missing_by_model.items():
            print(f"\n  # Add to {model_name} model:")
            for field in sorted(fields):
                field_type = suggest_field_type(field)
                print(f"  {field} = {field_type}")
    
    return missing_by_model

def suggest_field_type(field_name):
    """Suggest appropriate field type based on field name"""
    field_name_lower = field_name.lower()
    
    if field_name.endswith('_id'):
        return "fields.Many2one('model.name', string='{}')".format(field_name.replace('_', ' ').title())
    elif field_name.endswith('_ids'):
        return "fields.One2many('model.name', 'field_name', string='{}')".format(field_name.replace('_', ' ').title())
    elif field_name.endswith('_date') or 'date' in field_name_lower:
        return "fields.Date(string='{}')".format(field_name.replace('_', ' ').title())
    elif field_name.endswith('_datetime') or 'datetime' in field_name_lower:
        return "fields.Datetime(string='{}')".format(field_name.replace('_', ' ').title())
    elif field_name.endswith('_count') or 'count' in field_name_lower:
        return "fields.Integer(string='{}', compute='_compute_{}')".format(field_name.replace('_', ' ').title(), field_name)
    elif any(word in field_name_lower for word in ['amount', 'cost', 'price', 'fee', 'rate', 'charge']):
        return "fields.Monetary(string='{}')".format(field_name.replace('_', ' ').title())
    elif any(word in field_name_lower for word in ['active', 'required', 'verified', 'enabled', 'auto_', 'is_', 'has_']):
        return "fields.Boolean(string='{}', default=True)".format(field_name.replace('_', ' ').title())
    elif 'percentage' in field_name_lower or field_name.endswith('_percent'):
        return "fields.Float(string='{}', digits=(5, 2))".format(field_name.replace('_', ' ').title())
    elif 'weight' in field_name_lower or 'quantity' in field_name_lower:
        return "fields.Float(string='{}')".format(field_name.replace('_', ' ').title())
    elif 'text' in field_name_lower or 'description' in field_name_lower or 'notes' in field_name_lower:
        return "fields.Text(string='{}')".format(field_name.replace('_', ' ').title())
    elif 'state' in field_name_lower or 'status' in field_name_lower:
        return "fields.Selection([('draft', 'Draft'), ('done', 'Done')], string='{}', default='draft')".format(field_name.replace('_', ' ').title())
    else:
        return "fields.Char(string='{}')".format(field_name.replace('_', ' ').title())

if __name__ == "__main__":
    os.chdir('/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management')
    analyze_missing_fields()
