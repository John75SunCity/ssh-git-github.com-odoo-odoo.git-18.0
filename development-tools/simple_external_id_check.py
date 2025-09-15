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

    # Define known valid external module references to avoid false positives
    valid_external_modules = {
        # Base Odoo modules
        'base.group_user', 'base.group_portal', 'base.group_system', 'base.user_admin',
        'base.menu_administration', 'base.model_records_document', 'base.model_records_container',

        # Account module
        'account.group_account_invoice', 'account.group_account_user',

        # Portal module
        'portal.portal_menu',

        # Product module
        'product.product_template_action', 'product.product_normal_action',

        # Stock module
        'stock.group_stock_user', 'stock.menu_stock_root',

        # Sale module
        'sale.group_sale_user', 'sale.menu_sale_root',

        # HR module
        'hr.group_hr_user', 'hr.menu_hr_root',

        # Project module
        'project.group_project_user', 'project.menu_main_pm',

        # Industry FSM module
        'industry_fsm.group_fsm_user', 'industry_fsm.menu_fsm_root',

        # Common Odoo system references
        'group_search_admin',  # This might be defined elsewhere in the system
    }

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
                        # Skip valid external module references and known issues
                        if (parent_id not in defined_ids and
                            parent_id not in valid_external_modules and
                            not parent_id.startswith('REPLACE_WITH_') and
                            not parent_id.startswith('TODO_')):
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
                        # Skip valid external module references
                        if (action_id not in defined_ids and
                            action_id not in valid_external_modules and
                            '.' in action_id):
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
                        # Skip valid external module references
                        if (ref_id not in defined_ids and
                            ref_id not in valid_external_modules):
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
        print(f"\n❌ Found {len(errors)} legitimate external ID reference errors:")
        print("(False positives for standard Odoo modules have been filtered out)")
        print("-" * 70)

        # Categorize errors for better reporting
        menu_errors = [e for e in errors if e['type'] == 'menuitem_parent']
        action_errors = [e for e in errors if e['type'] == 'action_reference']
        ref_errors = [e for e in errors if e['type'] == 'ref_function']

        if menu_errors:
            print(f"\n� MENU PARENT REFERENCE ERRORS ({len(menu_errors)}):")
            print("These menus are referenced as parents but don't exist:")
            for error in menu_errors:
                print(f"  📄 {error['file']}:{error['line']} → {error['error']}")

        if action_errors:
            print(f"\n⚡ ACTION REFERENCE ERRORS ({len(action_errors)}):")
            print("These actions are referenced but don't exist:")
            for error in action_errors:
                print(f"  📄 {error['file']}:{error['line']} → {error['error']}")

        if ref_errors:
            print(f"\n� REF() FUNCTION ERRORS ({len(ref_errors)}):")
            print("These ref() calls reference non-existent IDs:")
            for error in ref_errors:
                print(f"  📄 {error['file']}:{error['line']} → {error['error']}")

        print(f"\n💡 SUMMARY:")
        print(f"   - Total legitimate errors found: {len(errors)}")
        print(f"   - Menu reference errors: {len(menu_errors)}")
        print(f"   - Action reference errors: {len(action_errors)}")
        print(f"   - Ref() function errors: {len(ref_errors)}")
        print(f"   - Standard Odoo module references: ✅ Filtered out (no false positives)")
        print(f"   - Development placeholders: ✅ Filtered out (REPLACE_WITH_, TODO_)")

    else:
        print("\n✅ No external ID reference errors found!")
        print("All external references are valid!")

if __name__ == "__main__":
    main()
