#!/usr/bin/env python3
"""
Model Name Mismatch Audit
==========================
Detects mismatches between _name in Python models and model references in XML views.
This is a critical issue that causes "Model not found" ParseErrors.
"""

import os
import re
import xml.etree.ElementTree as ET

def extract_model_names_from_python():
    """Extract all _name definitions from Python model files"""
    models_dir = "records_management/models"
    model_names = {}
    
    print("🔍 Extracting model names from Python files...")
    
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            filepath = os.path.join(models_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find _name definitions
                name_matches = re.findall(r'_name\s*=\s*["\']([^"\']+)["\']', content)
                for model_name in name_matches:
                    model_names[model_name] = filename
                    
            except Exception as e:
                print(f"❌ Error reading {filepath}: {e}")
    
    return model_names

def extract_model_references_from_xml():
    """Extract all model references from XML view files"""
    views_dir = "records_management/views"
    model_references = {}
    
    print("🔍 Extracting model references from XML files...")
    
    for filename in os.listdir(views_dir):
        if filename.endswith('.xml'):
            filepath = os.path.join(views_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find model references in XML
                model_matches = re.findall(r'<field name="model">([^<]+)</field>', content)
                for model_name in model_matches:
                    if model_name not in model_references:
                        model_references[model_name] = []
                    model_references[model_name].append(filename)
                    
            except Exception as e:
                print(f"❌ Error reading {filepath}: {e}")
    
    return model_references

def find_model_mismatches():
    """Find mismatches between Python model names and XML references"""
    print("🔍 MODEL NAME MISMATCH AUDIT")
    print("=" * 50)
    
    python_models = extract_model_names_from_python()
    xml_references = extract_model_references_from_xml()
    
    print(f"\n📊 Found {len(python_models)} Python models")
    print(f"📊 Found {len(xml_references)} XML model references")
    
    # Find XML references without corresponding Python models
    missing_models = []
    for xml_model in xml_references:
        if xml_model not in python_models:
            missing_models.append((xml_model, xml_references[xml_model]))
    
    # Find Python models not referenced in XML
    unreferenced_models = []
    for python_model in python_models:
        if python_model not in xml_references:
            unreferenced_models.append((python_model, python_models[python_model]))
    
    # Report results
    print(f"\n🚨 CRITICAL ISSUES: {len(missing_models)} missing model definitions")
    if missing_models:
        for model_name, xml_files in missing_models:
            print(f"   ❌ Model '{model_name}' referenced in XML but not defined in Python:")
            for xml_file in xml_files:
                print(f"      - {xml_file}")
    
    print(f"\n⚠️  WARNINGS: {len(unreferenced_models)} unreferenced models")
    if unreferenced_models:
        for model_name, python_file in unreferenced_models:
            print(f"   ⚠️  Model '{model_name}' defined in {python_file} but not used in views")
    
    print(f"\n✅ VALID REFERENCES: {len(set(xml_references.keys()) & set(python_models.keys()))}")
    
    return missing_models, unreferenced_models

def show_detailed_model_mapping():
    """Show detailed mapping between Python models and XML references"""
    python_models = extract_model_names_from_python()
    xml_references = extract_model_references_from_xml()
    
    print(f"\n📋 DETAILED MODEL MAPPING")
    print("=" * 50)
    
    all_models = set(python_models.keys()) | set(xml_references.keys())
    
    for model in sorted(all_models):
        python_file = python_models.get(model, "❌ NOT DEFINED")
        xml_files = xml_references.get(model, ["❌ NOT REFERENCED"])
        
        status = "✅" if model in python_models and model in xml_references else "❌"
        print(f"\n{status} {model}")
        print(f"   Python: {python_file}")
        print(f"   XML: {', '.join(xml_files)}")

if __name__ == "__main__":
    os.chdir("/workspaces/ssh-git-github.com-odoo-odoo.git-18.0")
    
    missing, unreferenced = find_model_mismatches()
    
    if missing:
        print(f"\n🔧 FIXES NEEDED:")
        print("To fix missing models, either:")
        print("1. Fix the _name in the Python model file")
        print("2. Update the model references in XML files")
        print("3. Create the missing model file")
    
    show_detailed_model_mapping()
    
    print(f"\n🎯 AUDIT COMPLETE")
    if missing:
        print("❌ Critical issues found - these WILL cause ParseError during module loading")
    else:
        print("✅ No model name mismatches detected")
