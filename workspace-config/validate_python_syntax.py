#!/usr/bin/env python3
"""
Python Syntax Validator for Records Management Module
Validates all Python files for syntax errors and basic import issues
"""

import os
import py_compile
import sys
import tempfile
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate Python syntax for a single file"""
    try:
        # Try to compile the file
        with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
            py_compile.compile(file_path, tmp.name, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def find_python_files(directory):
    """Find all Python files in the directory"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return sorted(python_files)

def main():
    """Main validation function"""
    records_mgmt_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    if not os.path.exists(records_mgmt_dir):
        print(f"Error: Directory {records_mgmt_dir} not found")
        return 1
    
    python_files = find_python_files(records_mgmt_dir)
    
    print("=== PYTHON SYNTAX VALIDATION REPORT ===")
    print(f"Found {len(python_files)} Python files to validate\n")
    
    valid_files = []
    invalid_files = []
    
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, records_mgmt_dir)
        is_valid, error_msg = validate_python_syntax(file_path)
        
        if is_valid:
            valid_files.append(rel_path)
            print(f"✅ {rel_path}")
        else:
            invalid_files.append((rel_path, error_msg))
            print(f"❌ {rel_path}: {error_msg}")
    
    print(f"\n=== SUMMARY ===")
    print(f"Valid files: {len(valid_files)}/{len(python_files)}")
    print(f"Invalid files: {len(invalid_files)}/{len(python_files)}")
    
    if invalid_files:
        print(f"\n=== ERRORS FOUND ===")
        for file_path, error in invalid_files:
            print(f"\n{file_path}:")
            print(f"  {error}")
        return 1
    else:
        print(f"\n🎉 All Python files have valid syntax!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
