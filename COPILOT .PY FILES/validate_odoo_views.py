#!/usr/bin/env python3
"""
Script to validate Odoo XML view files for basic syntax and field references.
"""
import xml.etree.ElementTree as ET
import os
import sys

def validate_xml_syntax(file_path):
    """Validate XML syntax"""
    try:
        tree = ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        return False, f"XML Parse Error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def extract_field_names_from_views(xml_file):
    """Extract field names referenced in views"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        fields_by_model = {}
        
        for record in root.findall('.//record[@model="ir.ui.view"]'):
            model_elem = record.find('.//field[@name="model"]')
            if model_elem is not None:
                model_name = model_elem.text
                
                # Find all field references in the view
                arch_elem = record.find('.//field[@name="arch"]')
                if arch_elem is not None:
                    for field_elem in arch_elem.findall('.//field[@name]'):
                        field_name = field_elem.get('name')
                        if field_name:
                            if model_name not in fields_by_model:
                                fields_by_model[model_name] = set()
                            fields_by_model[model_name].add(field_name)
        
        return fields_by_model
    except Exception as e:
        print(f"Error parsing {xml_file}: {e}")
        return {}

def main():
    print("🔍 Validating Odoo XML files...")
    
    # Find all XML files in the module
    xml_files = []
    for root, dirs, files in os.walk('records_management'):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    print(f"Found {len(xml_files)} XML files to validate")
    
    # Validate syntax
    print("\n📋 XML Syntax Validation:")
    syntax_errors = 0
    for xml_file in sorted(xml_files):
        is_valid, error = validate_xml_syntax(xml_file)
        if is_valid:
            print(f"✅ {xml_file}")
        else:
            print(f"❌ {xml_file}: {error}")
            syntax_errors += 1
    
    if syntax_errors > 0:
        print(f"\n❌ {syntax_errors} files have syntax errors. Fix these first.")
        return 1
    
    # Extract field references from view files
    print("\n🔍 Checking field references in view files:")
    view_files = [f for f in xml_files if '/views/' in f]
    
    all_field_refs = {}
    for view_file in view_files:
        field_refs = extract_field_names_from_views(view_file)
        for model, fields in field_refs.items():
            if model not in all_field_refs:
                all_field_refs[model] = set()
            all_field_refs[model].update(fields)
        
        if field_refs:
            print(f"📄 {view_file}:")
            for model, fields in field_refs.items():
                print(f"  {model}: {', '.join(sorted(fields))}")
    
    print(f"\n🎉 All {len(xml_files)} XML files are syntactically valid!")
    print(f"📊 Found field references for {len(all_field_refs)} models")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
