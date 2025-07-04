#!/usr/bin/env python3
"""
Simple module validation script to check for common issues
"""
import os
import xml.etree.ElementTree as ET
from pathlib import Path

def validate_xml_files(module_path):
    """Validate XML files in the module"""
    xml_files = []
    
    # Find all XML files
    for root, dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    print(f"Found {len(xml_files)} XML files")
    
    for xml_file in xml_files:
        try:
            ET.parse(xml_file)
            print(f"✓ {xml_file} - Valid XML")
        except ET.ParseError as e:
            print(f"✗ {xml_file} - Parse Error: {e}")
        except Exception as e:
            print(f"✗ {xml_file} - Error: {e}")

def validate_python_files(module_path):
    """Basic validation of Python files"""
    py_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk(module_path):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    print(f"\nFound {len(py_files)} Python files")
    
    for py_file in py_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Basic syntax check
                compile(content, py_file, 'exec')
            print(f"✓ {py_file} - Valid Python")
        except SyntaxError as e:
            print(f"✗ {py_file} - Syntax Error: {e}")
        except Exception as e:
            print(f"✗ {py_file} - Error: {e}")

def main():
    module_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-8.0/records_management'
    
    if not os.path.exists(module_path):
        print(f"Module path not found: {module_path}")
        return
    
    print(f"Validating module: {module_path}")
    print("=" * 50)
    
    validate_xml_files(module_path)
    validate_python_files(module_path)
    
    print("\nValidation complete!")

if __name__ == "__main__":
    main()
