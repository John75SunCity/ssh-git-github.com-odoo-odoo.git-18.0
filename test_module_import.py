#!/usr/bin/env python3
"""
Test script to verify the records_management module can be imported successfully.
This simulates the basic validation checks that Odoo.sh would perform.
"""

import os
import sys
import ast

def test_manifest():
    """Test the manifest file for proper structure."""
    print("Testing __manifest__.py...")
    
    manifest_path = "records_management/__manifest__.py"
    if not os.path.exists(manifest_path):
        print("❌ FAIL: __manifest__.py not found")
        return False
        
    try:
        with open(manifest_path, 'r') as f:
            manifest_content = f.read()
        
        # Parse as Python AST
        ast.parse(manifest_content)
        print("✅ PASS: __manifest__.py syntax is valid")
        
        # Try to evaluate the manifest dictionary
        manifest = eval(manifest_content)
        
        # Check required fields
        required_fields = ['name', 'version', 'depends', 'data']
        for field in required_fields:
            if field not in manifest:
                print(f"❌ FAIL: Missing required field '{field}' in manifest")
                return False
        
        print(f"✅ PASS: Manifest has all required fields")
        print(f"  - Name: {manifest['name']}")
        print(f"  - Version: {manifest['version']}")
        print(f"  - Dependencies: {manifest['depends']}")
        print(f"  - Data files: {len(manifest['data'])} files")
        
        return True
        
    except Exception as e:
        print(f"❌ FAIL: Error parsing __manifest__.py: {e}")
        return False

def test_python_files():
    """Test that all Python files can be parsed."""
    print("\nTesting Python files...")
    
    python_files = []
    for root, dirs, files in os.walk('records_management'):
        for file in files:
            if file.endswith('.py') and not file.startswith('__pycache__'):
                python_files.append(os.path.join(root, file))
    
    all_valid = True
    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                content = f.read()
            ast.parse(content)
            print(f"✅ PASS: {py_file}")
        except Exception as e:
            print(f"❌ FAIL: {py_file} - {e}")
            all_valid = False
    
    return all_valid

def test_xml_files():
    """Test that all XML files are well-formed."""
    print("\nTesting XML files...")
    
    xml_files = []
    for root, dirs, files in os.walk('records_management'):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    all_valid = True
    for xml_file in xml_files:
        try:
            import xml.etree.ElementTree as ET
            ET.parse(xml_file)
            print(f"✅ PASS: {xml_file}")
        except Exception as e:
            print(f"❌ FAIL: {xml_file} - {e}")
            all_valid = False
    
    return all_valid

def test_security_groups():
    """Test that all referenced security groups are defined."""
    print("\nTesting security groups...")
    
    # Read security file
    try:
        import xml.etree.ElementTree as ET
        security_tree = ET.parse('records_management/security/records_management_security.xml')
        security_root = security_tree.getroot()
        
        # Find all defined groups
        defined_groups = set()
        for record in security_root.findall('.//record[@model="res.groups"]'):
            group_id = record.get('id')
            if group_id:
                defined_groups.add(f"records_management.{group_id}")
        
        print(f"Defined groups: {sorted(defined_groups)}")
        
        # Find all referenced groups in menu files
        referenced_groups = set()
        menu_file = 'records_management/views/records_management_menus.xml'
        if os.path.exists(menu_file):
            with open(menu_file, 'r') as f:
                content = f.read()
            
            import re
            group_refs = re.findall(r'groups="(records_management\.[^"]+)"', content)
            referenced_groups.update(group_refs)
        
        # Check stock_lot_views.xml too
        stock_file = 'records_management/views/stock_lot_views.xml'
        if os.path.exists(stock_file):
            with open(stock_file, 'r') as f:
                content = f.read()
            
            group_refs = re.findall(r'groups="(records_management\.[^"]+)"', content)
            referenced_groups.update(group_refs)
        
        print(f"Referenced groups: {sorted(referenced_groups)}")
        
        # Check if all referenced groups are defined
        missing_groups = referenced_groups - defined_groups
        if missing_groups:
            print(f"❌ FAIL: Missing group definitions: {missing_groups}")
            return False
        else:
            print("✅ PASS: All referenced security groups are defined")
            return True
            
    except Exception as e:
        print(f"❌ FAIL: Error checking security groups: {e}")
        return False

def main():
    """Run all tests."""
    print("=== Records Management Module Validation ===\n")
    
    # Change to the workspace directory
    os.chdir('/workspaces/ssh-git-github.com-odoo-odoo.git-8.0')
    
    tests = [
        test_manifest,
        test_python_files,
        test_xml_files,
        test_security_groups,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ FAIL: Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("=== SUMMARY ===")
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Module should install successfully!")
        return True
    else:
        print("❌ Some tests failed - module may have installation issues")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
