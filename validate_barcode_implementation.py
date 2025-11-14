#!/usr/bin/env python3
"""
Quick Barcode Implementation Validation Script

Checks basic syntax and structure of newly created barcode files.
"""

import os
import sys
import ast
import xml.etree.ElementTree as ET

def check_python_syntax(filepath):
    """Validate Python file syntax."""
    print(f"Checking Python: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        print(f"  ✅ Valid Python syntax")
        return True
    except SyntaxError as e:
        print(f"  ❌ Syntax Error: {e}")
        return False

def check_xml_syntax(filepath):
    """Validate XML file syntax."""
    print(f"Checking XML: {filepath}")
    try:
        ET.parse(filepath)
        print(f"  ✅ Valid XML syntax")
        return True
    except ET.ParseError as e:
        print(f"  ❌ Parse Error: {e}")
        return False

def check_javascript_basic(filepath):
    """Basic JavaScript validation (checks for common syntax errors)."""
    print(f"Checking JavaScript: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Basic checks
        if content.count('{') != content.count('}'):
            print(f"  ⚠️  Warning: Mismatched curly braces")
            return False
        if content.count('(') != content.count(')'):
            print(f"  ⚠️  Warning: Mismatched parentheses")
            return False
        if content.count('[') != content.count(']'):
            print(f"  ⚠️  Warning: Mismatched square brackets")
            return False
        
        print(f"  ✅ Basic JavaScript syntax OK")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    """Main validation routine."""
    print("=" * 60)
    print("BARCODE IMPLEMENTATION VALIDATION")
    print("=" * 60)
    print()
    
    base_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"
    
    files_to_check = {
        'python': [
            f"{base_path}/models/barcode_standard_commands.py",
        ],
        'xml': [
            f"{base_path}/views/barcode_standard_commands_buttons.xml",
            f"{base_path}/templates/portal_barcode_templates.xml",
            f"{base_path}/report/barcode_reports.xml",
        ],
        'javascript': [
            f"{base_path}/static/src/js/barcode_command_handler.js",
        ]
    }
    
    all_valid = True
    
    # Check Python files
    print("PYTHON FILES")
    print("-" * 60)
    for filepath in files_to_check['python']:
        if os.path.exists(filepath):
            if not check_python_syntax(filepath):
                all_valid = False
        else:
            print(f"❌ File not found: {filepath}")
            all_valid = False
        print()
    
    # Check XML files
    print("XML FILES")
    print("-" * 60)
    for filepath in files_to_check['xml']:
        if os.path.exists(filepath):
            if not check_xml_syntax(filepath):
                all_valid = False
        else:
            print(f"❌ File not found: {filepath}")
            all_valid = False
        print()
    
    # Check JavaScript files
    print("JAVASCRIPT FILES")
    print("-" * 60)
    for filepath in files_to_check['javascript']:
        if os.path.exists(filepath):
            if not check_javascript_basic(filepath):
                all_valid = False
        else:
            print(f"❌ File not found: {filepath}")
            all_valid = False
        print()
    
    # Check CSS file exists
    print("CSS FILES")
    print("-" * 60)
    css_file = f"{base_path}/static/src/css/barcode_scanner.css"
    if os.path.exists(css_file):
        print(f"✅ CSS file exists: {css_file}")
    else:
        print(f"❌ CSS file not found: {css_file}")
        all_valid = False
    print()
    
    # Summary
    print("=" * 60)
    if all_valid:
        print("✅ ALL VALIDATIONS PASSED")
        print("=" * 60)
        return 0
    else:
        print("❌ SOME VALIDATIONS FAILED")
        print("=" * 60)
        return 1

if __name__ == '__main__':
    sys.exit(main())
