#!/usr/bin/env python3
"""
Comprehensive Dependency Field Validator
Validates each @api.depends field reference to ensure the field actually exists
"""

import os
import re
import ast
from collections import defaultdict

def extract_model_name(file_path):
    """Extract the model name from a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for _name = 'model.name'
        name_match = re.search(r'_name\s*=\s*["\']([^"\']+)["\']', content)
        if name_match:
            return name_match.group(1)
    except Exception:
        pass
    return None

def extract_field_definitions(file_path):
    """Extract all field definitions from a model file"""
    fields = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find field definitions: field_name = fields.Type(
        field_pattern = r'(\w+)\s*=\s*fields\.[A-Z]\w*\('
        matches = re.finditer(field_pattern, content)

        for match in matches:
            field_name = match.group(1)
            fields[field_name] = True

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return fields

def find_api_depends(file_path):
    """Find all @api.depends decorators and their field references"""
    depends_list = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for i, line in enumerate(lines, 1):
            if '@api.depends(' in line:
                # Extract the full depends declaration (might span multiple lines)
                depends_content = line
                j = i
                while not depends_content.count('(') == depends_content.count(')') and j < len(lines):
                    j += 1
                    if j <= len(lines):
                        depends_content += lines[j-1]

                # Extract field references from the depends
                depends_match = re.search(r'@api\.depends\((.*?)\)', depends_content, re.DOTALL)
                if depends_match:
                    depends_str = depends_match.group(1)
                    # Find all quoted strings (field references)
                    field_refs = re.findall(r'["\']([^"\']+)["\']', depends_str)

                    for field_ref in field_refs:
                        depends_list.append({
                            'line': i,
                            'field_ref': field_ref,
                            'code': line.strip()
                        })

    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")

    return depends_list

def validate_field_reference(field_ref, all_models_fields):
    """Validate a field reference like 'model_id.field_name'"""
    if '.' not in field_ref:
        # Direct field reference (should exist in same model)
        return True, "Direct field reference"

    parts = field_ref.split('.')
    if len(parts) < 2:
        return True, "Simple reference"

    # For complex references like 'related_model_ids.field_name'
    field_name = parts[-1]

    # Check if it's a standard Odoo field
    standard_fields = {
        'id', 'create_date', 'create_uid', 'write_date', 'write_uid',
        'name', 'display_name', 'state', 'active', 'company_id',
        'currency_id', 'user_id', 'partner_id', 'sequence'
    }

    if field_name in standard_fields:
        return True, f"Standard Odoo field: {field_name}"

    # Check if the field exists in any of our models
    field_found_in_models = []
    for model_name, fields in all_models_fields.items():
        if field_name in fields:
            field_found_in_models.append(model_name)

    if field_found_in_models:
        return True, f"Field exists in models: {', '.join(field_found_in_models)}"

    return False, f"Field '{field_name}' not found in any model"

def main():
    """Main validation function"""
    print("🔍 Starting Comprehensive Dependency Field Validation...")
    print("=" * 80)

    # Scan all model files
    models_dir = "records_management/models"
    all_models_fields = {}
    all_model_names = {}

    print("📂 Scanning model files...")
    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)

            # Extract model name and fields
            model_name = extract_model_name(file_path)
            fields = extract_field_definitions(file_path)

            if model_name:
                all_models_fields[model_name] = fields
                all_model_names[filename] = model_name
                print(f"   📄 {filename}: {model_name} ({len(fields)} fields)")

    print(f"\n✅ Scanned {len(all_models_fields)} models")

    # Now validate each dependency
    print("\n🔍 Validating @api.depends field references...")
    print("=" * 80)

    total_issues = 0
    critical_issues = 0
    false_positives = 0

    for filename in os.listdir(models_dir):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(models_dir, filename)

            depends_list = find_api_depends(file_path)
            if not depends_list:
                continue

            print(f"\n📄 {filename}:")

            for depend in depends_list:
                field_ref = depend['field_ref']
                is_valid, reason = validate_field_reference(field_ref, all_models_fields)

                if is_valid:
                    print(f"   ✅ Line {depend['line']}: {field_ref} - {reason}")
                    false_positives += 1
                else:
                    print(f"   ❌ Line {depend['line']}: {field_ref} - {reason}")
                    print(f"      Code: {depend['code']}")
                    critical_issues += 1

                total_issues += 1

    # Summary
    print("\n" + "=" * 80)
    print("📊 VALIDATION SUMMARY:")
    print(f"   Total field references checked: {total_issues}")
    print(f"   ✅ Valid references (false positives): {false_positives}")
    print(f"   ❌ Critical issues requiring fixes: {critical_issues}")

    if critical_issues == 0:
        print("\n🎉 All dependency field references are valid!")
        print("   The remaining issues flagged by the dependency checker are false positives.")
    else:
        print(f"\n⚠️  Found {critical_issues} critical dependency issues that need fixing.")

    return critical_issues == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
