#!/usr/bin/env python3
"""
Comprehensive Loading Order Analysis for Records Management Module
Checks for potential loading order issues between menu files and action definitions
"""

import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET

def analyze_loading_order():
    """Analyze loading order issues in the Records Management module"""

    module_path = Path("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management")

    # Read manifest to get loading order
    manifest_path = module_path / "__manifest__.py"
    with open(manifest_path, 'r') as f:
        manifest_content = f.read()

    # Extract data files in loading order
    data_files = []
    data_match = re.search(r'"data":\s*\[(.*?)\]', manifest_content, re.DOTALL)
    if data_match:
        data_content = data_match.group(1)
        # Extract file paths
        file_matches = re.findall(r'"([^"]+)"', data_content)
        data_files = [f for f in file_matches if f.endswith('.xml')]

    print("📋 MANIFEST LOADING ORDER:")
    for i, file in enumerate(data_files, 1):
        print(f"  {i:2d}: {file}")
    print()

    # Find menu files and their positions
    menu_files = [f for f in data_files if 'menu' in f.lower()]
    menu_positions = {file: i for i, file in enumerate(data_files) if 'menu' in file.lower()}

    print("🎯 MENU FILES AND POSITIONS:")
    for menu_file, position in menu_positions.items():
        print(f"  {position:2d}: {menu_file}")
    print()

    # Analyze each menu file for action references
    issues_found = []
    actions_found = []

    for menu_file in menu_files:
        menu_path = module_path / "views" / menu_file
        if not menu_path.exists():
            continue

        print(f"🔍 ANALYZING: {menu_file}")
        menu_position = menu_positions[menu_file]

        try:
            tree = ET.parse(menu_path)
            root = tree.getroot()

            # Find all action references in menu items
            for menuitem in root.findall(".//menuitem"):
                action = menuitem.get('action')
                if action and not action.startswith('/'):  # Skip URL actions
                    actions_found.append(action)

                    # Check if this action is defined in a file that loads after the menu
                    action_found = False
                    action_definition_file = None

                    for file in data_files[menu_position:]:  # Files that load after menu
                        file_path = module_path / "views" / file
                        if file_path.exists():
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    if f'id="{action}"' in content and 'model="ir.actions.act_window"' in content:
                                        action_found = True
                                        action_definition_file = file
                                        break
                            except Exception as e:
                                continue

                    if action_found:
                        issues_found.append({
                            'menu_file': menu_file,
                            'menu_position': menu_position,
                            'action': action,
                            'definition_file': action_definition_file,
                            'definition_position': data_files.index(action_definition_file),
                            'severity': 'HIGH' if data_files.index(action_definition_file) > menu_position else 'OK'
                        })

        except Exception as e:
            print(f"  ❌ Error parsing {menu_file}: {e}")

    print("\n📊 ANALYSIS RESULTS:")
    print("=" * 60)

    if not issues_found:
        print("✅ NO LOADING ORDER ISSUES FOUND!")
        print("   All actions referenced in menus are properly defined before menu loading.")
    else:
        high_priority = [issue for issue in issues_found if issue['severity'] == 'HIGH']
        if high_priority:
            print(f"🚨 HIGH PRIORITY ISSUES ({len(high_priority)}):")
            for issue in high_priority:
                print(f"  ❌ {issue['action']} in {issue['menu_file']} (pos {issue['menu_position']})")
                print(f"     → Defined in {issue['definition_file']} (pos {issue['definition_position']})")
                print("     → ACTION: Move action definition to menu file or earlier loading file")
        else:
            print("✅ NO HIGH PRIORITY ISSUES!")

        ok_issues = [issue for issue in issues_found if issue['severity'] == 'OK']
        if ok_issues:
            print(f"\n⚠️ OK ISSUES ({len(ok_issues)}):")
            for issue in ok_issues:
                print(f"  ✓ {issue['action']} - properly ordered")

    print(f"\n📈 SUMMARY:")
    print(f"   • Menu files analyzed: {len(menu_files)}")
    print(f"   • Actions referenced: {len(set(actions_found))}")
    print(f"   • Issues found: {len(issues_found)}")
    print(f"   • High priority: {len([i for i in issues_found if i['severity'] == 'HIGH'])}")

    return issues_found

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE LOADING ORDER ANALYSIS")
    print("=" * 60)
    issues = analyze_loading_order()

    if issues:
        print("\n💡 RECOMMENDATIONS:")
        print("   1. Move action definitions to menu files for critical actions")
        print("   2. Ensure menu files load before view files with action definitions")
        print("   3. Use the validation script before committing changes")
        print("   4. Test module loading after making changes")
    else:
        print("\n🎉 MODULE LOADING ORDER IS OPTIMAL!")
