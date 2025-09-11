#!/usr/bin/env python3
"""
XML Syntax Validator for Records Management Module
Validates all XML files for well-formed XML syntax
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

def validate_xml_syntax(file_path):
    """Validate XML syntax for a single file"""
    try:
        ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def find_xml_files(directory):
    """Find all XML files in the directory"""
    xml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    return sorted(xml_files)

def main():
    """Main validation function"""
    records_mgmt_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    if not os.path.exists(records_mgmt_dir):
        print(f"Error: Directory {records_mgmt_dir} not found")
        return 1
    
    xml_files = find_xml_files(records_mgmt_dir)
    
    print("=== XML SYNTAX VALIDATION REPORT ===")
    print(f"Found {len(xml_files)} XML files to validate\n")
    
    valid_files = []
    invalid_files = []
    
    for file_path in xml_files:
        rel_path = os.path.relpath(file_path, records_mgmt_dir)
        is_valid, error_msg = validate_xml_syntax(file_path)
        
        if is_valid:
            valid_files.append(rel_path)
            print(f"✅ {rel_path}")
        else:
            invalid_files.append((rel_path, error_msg))
            print(f"❌ {rel_path}: {error_msg}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Valid files: {len(valid_files)}/{len(xml_files)}")
    print(f"Invalid files: {len(invalid_files)}/{len(xml_files)}")
    
    if invalid_files:
        print(f"\n=== ERRORS FOUND ===")
        for file_path, error in invalid_files:
            print(f"\n{file_path}:")
            print(f"  {error}")
        return 1
    else:
        print(f"\n🎉 All XML files are well-formed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
