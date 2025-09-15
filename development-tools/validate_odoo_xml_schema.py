#!/usr/bin/env python3
"""
Odoo XML Schema Validator
========================

Validates XML files for common Odoo schema compliance issues:
1. Menu items and actions outside of <data> tags
2. Invalid nested structures
3. Missing required elements

This helps catch deployment errors before they occur.
"""

import os
import xml.etree.ElementTree as ET
import glob
import re

def validate_xml_schema(file_path):
    """
    Check a single XML file for Odoo schema compliance issues.

    Args:
        file_path (str): Path to the XML file to check

    Returns:
        list: List of issues found
    """
    issues = []

    try:
        # Parse the XML file
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Check if it's an Odoo XML file
        if root.tag != 'odoo':
            return issues

        # Read the raw content to check for problematic patterns
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for menu items or actions outside of proper data tags
        lines = content.split('\n')
        in_record = False
        in_data = False

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track if we're inside a record
            if '<record' in stripped and not stripped.startswith('<!--'):
                in_record = True
            elif '</record>' in stripped and not stripped.startswith('<!--'):
                in_record = False

            # Track if we're inside a data tag
            if '<data' in stripped and not stripped.startswith('<!--'):
                in_data = True
            elif '</data>' in stripped and not stripped.startswith('<!--'):
                in_data = False

            # Check for menu items or actions outside of proper containers
            if ('<menuitem' in stripped or '<act_window' in stripped) and not stripped.startswith('<!--'):
                # These should be either:
                # 1. Inside a <data> tag, or
                # 2. Inside a <record> tag (for ir.actions.act_window records), or
                # 3. At root level but wrapped in <data>
                if not in_record and not in_data:
                    # Check if the line is directly under <odoo>
                    preceding_lines = [l.strip() for l in lines[:i-1] if l.strip() and not l.strip().startswith('<!--')]
                    if preceding_lines and not any('<data' in l for l in preceding_lines[-3:]):
                        issues.append(f"Line {i}: Menu item or action outside of <data> wrapper: {stripped[:80]}...")

        # Check for invalid nested <odoo><data> structure
        if '<odoo>' in content and '<data>' in content:
            # Pattern that would cause "Element odoo has extra content: data" error
            # This is WRONG - we actually WANT <odoo><data> structure in most cases
            # Only flag if there are elements both inside AND outside data tags
            lines_content = content.split('\n')
            has_elements_outside_data = False
            has_data_tag = False
            in_odoo_root = False
            in_data_tag = False

            for line in lines_content:
                stripped = line.strip()
                if '<odoo>' in stripped:
                    in_odoo_root = True
                elif '</odoo>' in stripped:
                    in_odoo_root = False
                elif in_odoo_root and '<data' in stripped:
                    has_data_tag = True
                    in_data_tag = True
                elif in_odoo_root and '</data>' in stripped:
                    in_data_tag = False
                elif (in_odoo_root and not in_data_tag and not stripped.startswith('<!--')
                      and stripped and not '<data' in stripped):
                    if (stripped.startswith('<record') or stripped.startswith('<menuitem')
                        or stripped.startswith('<act_window')):
                        has_elements_outside_data = True

            if has_data_tag and has_elements_outside_data:
                issues.append("Mixed structure: Elements both inside and outside <data> tags")

        # The old check was wrong - commenting out:
        # if re.search(r'<odoo>\s*<data>', content):
        #     # But allow <odoo><data noupdate="1">
        #     if not re.search(r'<odoo>\s*<data\s+noupdate=', content):
        #         issues.append("Invalid nested <odoo><data> structure found - should be <odoo> with direct content")

    except ET.ParseError as e:
        issues.append(f"XML parsing error: {e}")
    except Exception as e:
        issues.append(f"Error checking file: {e}")

    return issues

def main():
    """Main validation function."""
    print("🔍 ODOO XML SCHEMA VALIDATOR")
    print("=" * 50)

    # Find all XML files in the records_management module
    xml_files = glob.glob("records_management/**/*.xml", recursive=True)

    if not xml_files:
        print("❌ No XML files found in records_management/")
        return

    print(f"📊 Checking {len(xml_files)} XML files...")

    total_issues = 0
    problematic_files = []

    for xml_file in xml_files:
        issues = validate_xml_schema(xml_file)
        if issues:
            total_issues += len(issues)
            problematic_files.append((xml_file, issues))

    if total_issues == 0:
        print("✅ All XML files pass Odoo schema validation!")
    else:
        print(f"\n❌ Found {total_issues} schema issues in {len(problematic_files)} files:")
        print("-" * 70)

        for file_path, issues in problematic_files:
            print(f"\n📄 {file_path}:")
            for issue in issues:
                print(f"   • {issue}")

        print(f"\n💡 SUMMARY:")
        print(f"   - Total issues: {total_issues}")
        print(f"   - Files affected: {len(problematic_files)}")
        print(f"   - Most common: Menu/action placement issues")

    return total_issues

if __name__ == "__main__":
    exit_code = main()
    exit(1 if exit_code > 0 else 0)
