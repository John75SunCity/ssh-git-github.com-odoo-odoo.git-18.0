#!/usr/bin/env python3
"""
Menu Reference Validation Script
Checks for missing menu references in Records Management module
"""
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

def extract_xml_ids(xml_file):
    """Extract all record IDs from an XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        ids = []

        for record in root.findall('.//record[@id]'):
            ids.append(record.get('id'))

        for menuitem in root.findall('.//menuitem[@id]'):
            ids.append(menuitem.get('id'))

        return ids
    except ET.ParseError as e:
        print(f"❌ XML Parse Error in {xml_file}: {e}")
        return []

def extract_menu_references(xml_file):
    """Extract all menu parent references from an XML file"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        references = []

        for menuitem in root.findall('.//menuitem[@parent]'):
            parent = menuitem.get('parent')
            references.append((parent, menuitem.get('id'), xml_file))

        return references
    except ET.ParseError as e:
        print(f"❌ XML Parse Error in {xml_file}: {e}")
        return []

def main():
    print("🔍 Menu Reference Validation")
    print("=" * 50)

    base_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    # Collect all defined menu IDs
    defined_ids = set()
    all_references = []

    # Scan all XML files
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)

                # Extract defined IDs
                ids = extract_xml_ids(file_path)
                defined_ids.update(ids)

                # Extract references
                refs = extract_menu_references(file_path)
                all_references.extend(refs)

    print(f"✅ Found {len(defined_ids)} defined menu IDs")
    print(f"🔍 Found {len(all_references)} menu references")
    print()

    # Check for missing references
    missing_refs = []
    for parent_ref, menu_id, file_path in all_references:
        # Handle module.id format
        if '.' in parent_ref:
            module, ref_id = parent_ref.split('.', 1)
            if module == 'records_management':
                # Local reference
                if ref_id not in defined_ids:
                    missing_refs.append((parent_ref, menu_id, file_path))
        else:
            # Direct reference
            if parent_ref not in defined_ids:
                missing_refs.append((parent_ref, menu_id, file_path))

    if missing_refs:
        print("❌ Missing Menu References Found:")
        for parent_ref, menu_id, file_path in missing_refs:
            print(f"  - {parent_ref} (referenced by {menu_id} in {os.path.basename(file_path)})")
    else:
        print("✅ All menu references are valid!")

    # Check specifically for the fixed references
    print("\n🔍 Checking Fixed References:")
    fixed_files = [
        'customer_inventory_report_views.xml',
        'revenue_forecast_line_views.xml'
    ]

    for file_name in fixed_files:
        file_path = os.path.join(base_path, 'views', file_name)
        if os.path.exists(file_path):
            refs = extract_menu_references(file_path)
            for parent_ref, menu_id, _ in refs:
                if 'menu_reports' in parent_ref:
                    print(f"  ✅ {file_name}: {menu_id} → {parent_ref}")

    return 0 if not missing_refs else 1

if __name__ == "__main__":
    exit(main())
