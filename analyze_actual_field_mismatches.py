#!/usr/bin/env python3
"""
Analyze ACTUAL field mismatches between models and views in Records Management.

This script properly separates:
1. View field references (actual fields that should exist in models)
2. Action configuration (res_model, view_mode, etc. - NOT model fields)
3. Infrastructure XML elements (field names like 'name', 'model', 'arch')

Previous audit tools incorrectly counted action configs as missing model fields.
"""

import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

def analyze_xml_file(xml_path):
    """
    Parse XML file and extract field references from view definitions only.
    Excludes action definitions and infrastructure elements.
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        view_fields = set()
        action_configs = set()
        
        # Find all record elements
        for record in root.findall('.//record'):
            model = record.get('model', '')
            
            if model == 'ir.ui.view':
                # This is a view definition - extract field references
                arch_field = record.find('.//field[@name="arch"]')
                if arch_field is not None:
                    # Extract field names from view arch
                    arch_content = ET.tostring(arch_field, encoding='unicode')
                    # Find field references: <field name="field_name"
                    field_matches = re.findall(r'<field\s+name="([^"]+)"', arch_content)
                    view_fields.update(field_matches)
                    
            elif model in ['ir.actions.act_window', 'ir.actions.server', 'ir.actions.client']:
                # This is an action definition - extract config fields
                for field in record.findall('.//field'):
                    field_name = field.get('name', '')
                    if field_name:
                        action_configs.add(field_name)
        
        return view_fields, action_configs
        
    except Exception as e:
        print(f"Error parsing {xml_path}: {e}")
        return set(), set()

def get_model_fields(model_path):
    """Extract field definitions from Python model file."""
    try:
        with open(model_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find field definitions using regex
        field_pattern = r'(\w+)\s*=\s*fields\.\w+'
        matches = re.findall(field_pattern, content)
        return set(matches)
        
    except Exception as e:
        print(f"Error reading {model_path}: {e}")
        return set()

def main():
    """Analyze shredding_service_bin as example of proper field analysis."""
    
    # Paths
    model_path = "records_management/models/shredding_service_bin.py"
    view_path = "records_management/views/shredding_service_bin_views.xml"
    
    if not os.path.exists(model_path):
        print(f"Model file not found: {model_path}")
        return
        
    if not os.path.exists(view_path):
        print(f"View file not found: {view_path}")
        return
    
    print("🔍 PROPER FIELD MISMATCH ANALYSIS")
    print("=" * 60)
    
    # Get model fields
    model_fields = get_model_fields(model_path)
    print(f"\n📝 Model Fields Found: {len(model_fields)}")
    print(f"Sample: {list(sorted(model_fields))[:5]}...")
    
    # Get view fields and action configs
    view_fields, action_configs = analyze_xml_file(view_path)
    
    print(f"\n👀 View Field References: {len(view_fields)}")
    print(f"Sample: {list(sorted(view_fields))[:5]}...")
    
    print(f"\n⚙️ Action Configurations: {len(action_configs)}")
    print(f"Sample: {list(sorted(action_configs))[:5]}...")
    
    # Find actual missing fields (view references not in model)
    missing_fields = view_fields - model_fields
    
    print(f"\n❌ ACTUAL Missing Fields: {len(missing_fields)}")
    if missing_fields:
        print("Fields referenced in views but not defined in model:")
        for field in sorted(missing_fields):
            print(f"  - {field}")
    else:
        print("✅ All view fields are properly defined in the model!")
    
    # Show what the old audit tool incorrectly counted
    print(f"\n🚨 What Old Audit Tool Incorrectly Counted:")
    print(f"  - Action configs as missing fields: {len(action_configs)}")
    print(f"  - These are NOT model fields: {list(sorted(action_configs))[:10]}...")
    
    print(f"\n✅ CONCLUSION:")
    print(f"  - Real missing fields: {len(missing_fields)}")
    print(f"  - False positives from old tool: {len(action_configs)}")
    print(f"  - This explains the 'hundreds of missing fields' confusion!")

if __name__ == "__main__":
    main()
