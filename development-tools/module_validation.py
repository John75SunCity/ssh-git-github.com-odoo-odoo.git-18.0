#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Records Management Module Validation Script
Checks manifest and Python syntax across the entire module
"""

import os
import ast
import sys
from pathlib import Path

def check_manifest(module_path):
    """Check if __manifest__.py is valid"""
    manifest_path = os.path.join(module_path, '__manifest__.py')
    
    if not os.path.exists(manifest_path):
        print("❌ __manifest__.py not found!")
        return False
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            content = f.read()
            manifest_data = ast.literal_eval(content)
        
        print("✅ __manifest__.py is valid!")
        
        # Check required fields
        required_fields = ['name', 'version', 'depends', 'data']
        missing_fields = [field for field in required_fields if field not in manifest_data]
        
        if missing_fields:
            print(f"⚠️  Missing required fields: {', '.join(missing_fields)}")
        else:
            print("✅ All required manifest fields present")
        
        # Show key info
        print(f"   Name: {manifest_data.get('name', 'Unknown')}")
        print(f"   Version: {manifest_data.get('version', 'Unknown')}")
        print(f"   Dependencies: {len(manifest_data.get('depends', []))} modules")
        print(f"   Data files: {len(manifest_data.get('data', []))} files")
        
        return True
        
    except Exception as e:
        print(f"❌ Manifest error: {e}")
        return False

def check_python_files(module_path):
    """Check Python syntax in all .py files"""
    print("\n🐍 PYTHON SYNTAX VALIDATION")
    print("-" * 50)
    
    syntax_errors = []
    valid_files = 0
    total_files = 0
    
    for root, dirs, files in os.walk(module_path):
        # Skip hidden directories and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            if file.endswith('.py'):
                total_files += 1
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, module_path)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        ast.parse(content)
                    
                    print(f"✅ {relative_path}")
                    valid_files += 1
                    
                except SyntaxError as e:
                    print(f"❌ {relative_path}: Syntax error at line {e.lineno}: {e.msg}")
                    syntax_errors.append((relative_path, e))
                    
                except Exception as e:
                    print(f"⚠️  {relative_path}: {e}")
                    syntax_errors.append((relative_path, e))
    
    print(f"\n📊 PYTHON FILES SUMMARY:")
    print(f"   Total files: {total_files}")
    print(f"   Valid files: {valid_files}")
    print(f"   Files with errors: {len(syntax_errors)}")
    
    return syntax_errors

def check_xml_files(module_path):
    """Check XML files for basic syntax"""
    print("\n📄 XML FILES VALIDATION")
    print("-" * 50)
    
    xml_errors = []
    valid_files = 0
    total_files = 0
    
    try:
        import xml.etree.ElementTree as ET
        
        for root, dirs, files in os.walk(module_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.xml'):
                    total_files += 1
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, module_path)
                    
                    try:
                        ET.parse(file_path)
                        print(f"✅ {relative_path}")
                        valid_files += 1
                        
                    except ET.ParseError as e:
                        print(f"❌ {relative_path}: XML error at line {e.lineno}: {e.msg}")
                        xml_errors.append((relative_path, e))
                        
                    except Exception as e:
                        print(f"⚠️  {relative_path}: {e}")
                        xml_errors.append((relative_path, e))
        
        print(f"\n📊 XML FILES SUMMARY:")
        print(f"   Total files: {total_files}")
        print(f"   Valid files: {valid_files}")
        print(f"   Files with errors: {len(xml_errors)}")
        
    except ImportError:
        print("⚠️  xml.etree.ElementTree not available, skipping XML validation")
        xml_errors = []
    
    return xml_errors

def check_model_imports(module_path):
    """Check model import order and dependencies"""
    print("\n🔗 MODEL IMPORTS VALIDATION")
    print("-" * 50)
    
    models_init_path = os.path.join(module_path, 'models', '__init__.py')
    
    if not os.path.exists(models_init_path):
        print("⚠️  models/__init__.py not found")
        return []
    
    try:
        with open(models_init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all import statements
        import_lines = []
        for line_num, line in enumerate(content.split('\n'), 1):
            line = line.strip()
            if line.startswith('from . import ') or line.startswith('from .'):
                import_lines.append((line_num, line))
        
        print(f"✅ Found {len(import_lines)} model imports")
        
        # Check if imported files exist
        missing_files = []
        for line_num, import_line in import_lines:
            if 'from . import ' in import_line:
                module_name = import_line.split('from . import ')[-1].strip()
                module_file = os.path.join(module_path, 'models', f'{module_name}.py')
                
                if not os.path.exists(module_file):
                    missing_files.append((line_num, module_name))
                    print(f"❌ Line {line_num}: Missing file {module_name}.py")
                else:
                    print(f"✅ {module_name}.py")
        
        if not missing_files:
            print("✅ All imported model files exist")
        
        return missing_files
        
    except Exception as e:
        print(f"❌ Error checking model imports: {e}")
        return []

def run_comprehensive_validation():
    """Run all validation checks"""
    
    # Get module path
    module_path = '/workspaces/ssh-git-github.com-odoo-odoo.git-18.0/records_management'
    
    if not os.path.exists(module_path):
        print(f"❌ Module path not found: {module_path}")
        return
    
    print("🔍 RECORDS MANAGEMENT MODULE VALIDATION")
    print("=" * 80)
    print(f"Module path: {module_path}")
    
    # Check manifest
    print("\n📋 MANIFEST VALIDATION")
    print("-" * 50)
    manifest_ok = check_manifest(module_path)
    
    # Check Python files
    python_errors = check_python_files(module_path)
    
    # Check XML files
    xml_errors = check_xml_files(module_path)
    
    # Check model imports
    import_errors = check_model_imports(module_path)
    
    # Overall summary
    print("\n🎯 OVERALL VALIDATION SUMMARY")
    print("=" * 80)
    
    total_errors = len(python_errors) + len(xml_errors) + len(import_errors)
    
    if manifest_ok and total_errors == 0:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("   ✅ Manifest is valid")
        print("   ✅ All Python files have valid syntax")
        print("   ✅ All XML files are well-formed")
        print("   ✅ All model imports are correct")
        print("\n   🚀 Module should install without syntax errors!")
        
    else:
        print("⚠️  VALIDATION ISSUES FOUND:")
        if not manifest_ok:
            print("   ❌ Manifest has issues")
        if python_errors:
            print(f"   ❌ {len(python_errors)} Python syntax errors")
        if xml_errors:
            print(f"   ❌ {len(xml_errors)} XML syntax errors")
        if import_errors:
            print(f"   ❌ {len(import_errors)} missing import files")
        
        print("\n🔧 FIX REQUIRED BEFORE INSTALLATION")
    
    # Detailed error report
    if total_errors > 0:
        print("\n📝 DETAILED ERROR REPORT")
        print("-" * 50)
        
        if python_errors:
            print("Python Errors:")
            for file_path, error in python_errors:
                print(f"  • {file_path}: {error}")
        
        if xml_errors:
            print("XML Errors:")
            for file_path, error in xml_errors:
                print(f"  • {file_path}: {error}")
        
        if import_errors:
            print("Import Errors:")
            for line_num, module_name in import_errors:
                print(f"  • Line {line_num}: Missing {module_name}.py")

if __name__ == "__main__":
    run_comprehensive_validation()
