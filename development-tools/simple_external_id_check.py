#!/usr/bin/env python3
"""
Simple External ID Reference Checker
Specifically looks for the "records_management.menu_root" error and other external ID reference issues
"""

import os
import re
import xml.etree.ElementTree as ET

def collect_defined_xml_ids():
    """Collect all XML IDs defined in the records_management module."""
    defined_ids = set()

    for root, dirs, files in os.walk("records_management"):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                try:
                    tree = ET.parse(file_path)
                    root_element = tree.getroot()

                    # Find all elements with 'id' attribute
                    for elem in root_element.iter():
                        if 'id' in elem.attrib:
                            xml_id = elem.attrib['id']
                            # Store both full module.id and just id
                            defined_ids.add(xml_id)
                            defined_ids.add(f"records_management.{xml_id}")

                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

    return defined_ids

def check_external_references():
    """Check for external ID references that don't exist."""
    print("🔍 Collecting all defined XML IDs...")
    defined_ids = collect_defined_xml_ids()
    print(f"📊 Found {len(defined_ids)} defined XML IDs")

    # Check if specific problem ID exists
    if "records_management.menu_root" in defined_ids:
        print("✅ records_management.menu_root is defined")
    else:
        print("❌ records_management.menu_root is NOT defined")
        # Check for similar names
        similar = [id for id in defined_ids if 'menu' in id.lower() and 'root' in id.lower()]
        if similar:
            print(f"🔍 Similar menu IDs found: {similar}")

    print("\n🔍 Checking all external ID references...")
    errors = []

    for root, dirs, files in os.walk("records_management"):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for parent references in menuitem
                    menuitem_pattern = r'<menuitem[^>]*parent="([^"]+)"'
                    for match in re.finditer(menuitem_pattern, content):
                        parent_id = match.group(1)
                        if parent_id not in defined_ids:
                            line_num = content[:match.start()].count('\n') + 1
                            errors.append({
                                'file': file_path,
                                'line': line_num,
                                'error': f"External ID not found: {parent_id}",
                                'type': 'menuitem_parent'
                            })

                    # Check for action references
                    action_pattern = r'action="([^"]+)"'
                    for match in re.finditer(action_pattern, content):
                        action_id = match.group(1)
                        if action_id not in defined_ids and '.' in action_id:
                            line_num = content[:match.start()].count('\n') + 1
                            errors.append({
                                'file': file_path,
                                'line': line_num,
                                'error': f"External action reference not found: {action_id}",
                                'type': 'action_reference'
                            })

                    # Check for ref() function calls
                    ref_pattern = r'ref\([\'"]([^\'"]+)[\'"]\)'
                    for match in re.finditer(ref_pattern, content):
                        ref_id = match.group(1)
                        if ref_id not in defined_ids:
                            line_num = content[:match.start()].count('\n') + 1
                            errors.append({
                                'file': file_path,
                                'line': line_num,
                                'error': f"External ref() ID not found: {ref_id}",
                                'type': 'ref_function'
                            })

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")

    return errors

def main():
    print("🔍 SIMPLE EXTERNAL ID REFERENCE CHECKER")
    print("=" * 50)

    errors = check_external_references()

    if errors:
        print(f"\n❌ Found {len(errors)} external ID reference errors:")
        print("-" * 50)

        for error in errors:
            print(f"📄 File: {error['file']}")
            print(f"📍 Line: {error['line']}")
            print(f"🚨 Error: {error['error']}")
            print(f"🏷️  Type: {error['type']}")
            print("-" * 30)
    else:
        print("\n✅ No external ID reference errors found!")

if __name__ == "__main__":
    main()
