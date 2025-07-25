#!/usr/bin/env python3
"""
Comprehensive Module Validation Report
Validates all aspects of the Records Management module
"""

import os
import sys
import py_compile
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate Python syntax for a single file"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.pyc', delete=True) as tmp:
            py_compile.compile(file_path, tmp.name, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def validate_xml_syntax(file_path):
    """Validate XML syntax for a single file"""
    try:
        ET.parse(file_path)
        return True, None
    except ET.ParseError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def find_files_by_extension(directory, extension):
    """Find all files with given extension in the directory"""
    files = []
    for root, dirs, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith(extension):
                files.append(os.path.join(root, filename))
    return sorted(files)

def validate_manifest(manifest_path):
    """Validate __manifest__.py file"""
    issues = []
    
    if not os.path.exists(manifest_path):
        return False, ["__manifest__.py file not found"]
    
    # Check Python syntax first
    is_valid, error = validate_python_syntax(manifest_path)
    if not is_valid:
        issues.append(f"Syntax error: {error}")
        return False, issues
    
    # Try to load the manifest
    try:
        with open(manifest_path, 'r') as f:
            content = f.read()
        
        # Basic checks
        if 'name' not in content:
            issues.append("Missing 'name' field")
        if 'version' not in content:
            issues.append("Missing 'version' field")
        if 'depends' not in content:
            issues.append("Missing 'depends' field")
        if 'data' not in content:
            issues.append("Missing 'data' field")
            
    except Exception as e:
        issues.append(f"Error reading manifest: {str(e)}")
    
    return len(issues) == 0, issues

def main():
    """Main validation function"""
    records_mgmt_dir = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    print("=" * 60)
    print("COMPREHENSIVE RECORDS MANAGEMENT MODULE VALIDATION")
    print("=" * 60)
    
    if not os.path.exists(records_mgmt_dir):
        print(f"❌ Error: Directory {records_mgmt_dir} not found")
        return 1
    
    all_valid = True
    
    # 1. Validate __manifest__.py
    print("\n1. 📋 MANIFEST VALIDATION")
    print("-" * 30)
    manifest_path = os.path.join(records_mgmt_dir, '__manifest__.py')
    manifest_valid, manifest_issues = validate_manifest(manifest_path)
    if manifest_valid:
        print("✅ __manifest__.py is valid")
    else:
        print("❌ __manifest__.py has issues:")
        for issue in manifest_issues:
            print(f"   - {issue}")
        all_valid = False
    
    # 2. Validate Python files
    print("\n2. 🐍 PYTHON SYNTAX VALIDATION")
    print("-" * 30)
    python_files = find_files_by_extension(records_mgmt_dir, '.py')
    python_valid = 0
    python_invalid = 0
    
    for file_path in python_files:
        rel_path = os.path.relpath(file_path, records_mgmt_dir)
        is_valid, error_msg = validate_python_syntax(file_path)
        
        if is_valid:
            python_valid += 1
        else:
            python_invalid += 1
            print(f"❌ {rel_path}: {error_msg}")
    
    if python_invalid == 0:
        print(f"✅ All {python_valid} Python files have valid syntax")
    else:
        print(f"❌ {python_invalid}/{len(python_files)} Python files have syntax errors")
        all_valid = False
    
    # 3. Validate XML files
    print("\n3. 📄 XML SYNTAX VALIDATION")
    print("-" * 30)
    xml_files = find_files_by_extension(records_mgmt_dir, '.xml')
    xml_valid = 0
    xml_invalid = 0
    
    for file_path in xml_files:
        rel_path = os.path.relpath(file_path, records_mgmt_dir)
        is_valid, error_msg = validate_xml_syntax(file_path)
        
        if is_valid:
            xml_valid += 1
        else:
            xml_invalid += 1
            print(f"❌ {rel_path}: {error_msg}")
    
    if xml_invalid == 0:
        print(f"✅ All {xml_valid} XML files are well-formed")
    else:
        print(f"❌ {xml_invalid}/{len(xml_files)} XML files have syntax errors")
        all_valid = False
    
    # 4. Check for our new paper recycling models
    print("\n4. 🆕 NEW PAPER RECYCLING MODELS")
    print("-" * 30)
    paper_models = [
        'models/paper_bale_recycling.py',
        'models/paper_load_shipment.py',
        'views/paper_bale_recycling_views.xml',
        'views/paper_load_shipment_views.xml',
        'views/paper_recycling_menus.xml'
    ]
    
    for model_file in paper_models:
        full_path = os.path.join(records_mgmt_dir, model_file)
        if os.path.exists(full_path):
            print(f"✅ {model_file} exists")
        else:
            print(f"❌ {model_file} missing")
            all_valid = False
    
    # 5. Check JavaScript assets
    print("\n5. 📱 JAVASCRIPT ASSETS")
    print("-" * 30)
    js_files = [
        'static/src/js/paper_load_truck_widget.js',
        'static/src/js/paper_load_progress_field.js'
    ]
    
    for js_file in js_files:
        full_path = os.path.join(records_mgmt_dir, js_file)
        if os.path.exists(full_path):
            print(f"✅ {js_file} exists")
        else:
            print(f"❌ {js_file} missing")
            all_valid = False
    
    # 6. Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if all_valid:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("\nThe Records Management module is ready for deployment:")
        print("✅ Python syntax is valid")
        print("✅ XML files are well-formed")
        print("✅ Manifest file is correct")
        print("✅ New paper recycling models are present")
        print("✅ JavaScript widgets are available")
        print("\n📋 Next steps:")
        print("   1. Test module installation in Odoo")
        print("   2. Verify truck widget functionality")
        print("   3. Test mobile integration features")
        return 0
    else:
        print("❌ VALIDATION FAILED!")
        print("Please fix the issues above before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
