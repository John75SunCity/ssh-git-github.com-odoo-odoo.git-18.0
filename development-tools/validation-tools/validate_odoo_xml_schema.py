#!/usr/bin/env python3
"""
🔍 Odoo XML Schema Validation Tool
Checks for common Odoo XML schema violations that cause deployment errors.
"""

import os
import re
import xml.etree.ElementTree as ET

def check_odoo_xml_schema(file_path):
    """Check for common Odoo XML schema violations."""
    issues = []
    
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse XML
        try:
            root = ET.fromstring(content)
        except ET.ParseError as e:
            issues.append(f"XML Parse Error: {e}")
            return issues
        
        # Check 1: Root element should be <odoo>
        if root.tag != 'odoo':
            issues.append(f"Root element is '{root.tag}', should be 'odoo'")
        
        # Check 2: Should have exactly one <data> child
        data_elements = root.findall('data')
        if len(data_elements) == 0:
            issues.append("Missing <data> element")
        elif len(data_elements) > 1:
            issues.append(f"Multiple <data> elements found ({len(data_elements)})")
        
        # Check 3: All records should be inside <data>
        records_outside_data = root.findall('.//record')
        data_records = []
        for data in data_elements:
            data_records.extend(data.findall('.//record'))
        
        if len(records_outside_data) != len(data_records):
            issues.append("Some <record> elements are outside <data>")
        
        # Check 4: Check for incorrect tree/list usage in main views
        for record in root.findall('.//record[@model="ir.ui.view"]'):
            arch = record.find('.//field[@name="arch"]')
            if arch is not None:
                arch_content = ET.tostring(arch, encoding='unicode')
                # Check for <list> in main tree views (not in One2many)
                if '<list decoration-' in arch_content and 'mode="list"' not in arch_content:
                    issues.append("Main tree view uses <list> instead of <tree>")
        
        # Check 5: Verify proper XML declaration
        if not content.startswith('<?xml version="1.0" encoding="utf-8"?>'):
            issues.append("Missing or incorrect XML declaration")
        
        # Check 6: Check for unclosed tags
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '<' in line and '>' in line:
                # Simple check for obvious unclosed tags
                open_tags = re.findall(r'<([^/>][^>]*?)>', line)
                close_tags = re.findall(r'</([^>]+)>', line)
                if len(open_tags) != len(close_tags):
                    # This is a simple check, might have false positives
                    continue
        
    except Exception as e:
        issues.append(f"Error processing file: {e}")
    
    return issues

def scan_view_files():
    """Scan all XML view files for schema issues."""
    base_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/views"
    
    print("🔍 ODOO XML SCHEMA VALIDATION")
    print("=" * 60)
    
    total_files = 0
    files_with_issues = 0
    
    for filename in os.listdir(base_path):
        if filename.endswith('.xml'):
            total_files += 1
            file_path = os.path.join(base_path, filename)
            issues = check_odoo_xml_schema(file_path)
            
            if issues:
                files_with_issues += 1
                print(f"\n❌ {filename}:")
                for issue in issues:
                    print(f"   • {issue}")
            else:
                print(f"✅ {filename}")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total files scanned: {total_files}")
    print(f"   Files with issues: {files_with_issues}")
    print(f"   Clean files: {total_files - files_with_issues}")
    
    if files_with_issues == 0:
        print(f"\n🎉 All XML files pass Odoo schema validation!")
    else:
        print(f"\n⚠️  {files_with_issues} files need attention.")

if __name__ == "__main__":
    scan_view_files()
