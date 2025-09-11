#!/usr/bin/env python3
"""
Quick validation script to check ParseError issues
"""
import os
import sys
import xml.etree.ElementTree as ET

def check_xml_file(xml_path):
    """Check XML file for syntax errors"""
    try:
        ET.parse(xml_path)
        print(f"✅ {xml_path} - XML syntax OK")
        return True
    except ET.ParseError as e:
        print(f"❌ {xml_path} - XML ParseError: {e}")
        return False
    except Exception as e:
        print(f"❌ {xml_path} - Error: {e}")
        return False

def check_python_file(py_path):
    """Check Python file for syntax errors"""
    try:
        with open(py_path, 'r') as f:
            content = f.read()
        compile(content, py_path, 'exec')
        print(f"✅ {py_path} - Python syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {py_path} - Syntax Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {py_path} - Error: {e}")
        return False

def main():
    print("🔍 Quick Records Management Validation")
    print("=" * 50)

    base_path = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management"

    # Check key files related to visitor POS wizard
    files_to_check = [
        "wizards/visitor_pos_wizard.py",
        "views/visitor_pos_wizard_views.xml",
        "__manifest__.py",
        "wizards/__init__.py"
    ]

    all_ok = True
    for file_path in files_to_check:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            if file_path.endswith('.xml'):
                result = check_xml_file(full_path)
            elif file_path.endswith('.py'):
                result = check_python_file(full_path)
            else:
                print(f"⚠️ {full_path} - Unknown file type")
                result = True
            all_ok = all_ok and result
        else:
            print(f"❌ {full_path} - File not found")
            all_ok = False

    print("=" * 50)
    if all_ok:
        print("✅ All checked files are valid!")
    else:
        print("❌ Issues found in one or more files")

    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())
