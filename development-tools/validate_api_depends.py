#!/usr/bin/env python3
"""
Comprehensive validation script for @api.depends across all models.
Checks that all referenced fields in @api.depends actually exist.
"""

import os
import re
import ast
import sys

def extract_model_fields(file_path):
    """Extract model name and field definitions from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract model name
        model_name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if not model_name_match:
            return None, {}, []

        model_name = model_name_match.group(1)

        # Extract field definitions
        fields = {}
        field_pattern = r"(\w+)\s*=\s*fields\.\w+"
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            fields[field_name] = True

        # Also check for inherited fields and computed fields
        inherit_pattern = r"_inherit\s*=\s*\[?['\"]([^'\"]+)['\"]"
        inherit_match = re.search(inherit_pattern, content)
        inherited_models = []
        if inherit_match:
            inherited_models.append(inherit_match.group(1))

        return model_name, fields, inherited_models
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, {}, []

def extract_api_depends(file_path):
    """Extract all @api.depends declarations from a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        depends_pattern = r"@api\.depends\(['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])*\)"
        depends = []

        for match in re.finditer(depends_pattern, content):
            # Get the full match to extract all dependencies
            full_match = match.group(0)
            # Extract all quoted strings from the depends
            field_refs = re.findall(r"['\"]([^'\"]+)['\"]", full_match)
            depends.extend(field_refs)

        # Also look for multi-line @api.depends
        multiline_pattern = r"@api\.depends\(((?:[^)]*\n)*[^)]*)\)"
        for match in re.finditer(multiline_pattern, content, re.MULTILINE):
            deps_content = match.group(1)
            field_refs = re.findall(r"['\"]([^'\"]+)['\"]", deps_content)
            depends.extend(field_refs)

        return depends
    except Exception as e:
        print(f"Error extracting depends from {file_path}: {e}")
        return []

def validate_field_reference(field_ref, model_fields, all_models):
    """Validate that a field reference exists."""
    if '.' not in field_ref:
        # Direct field reference
        return field_ref in model_fields

    # Related field reference like 'partner_id.name'
    parts = field_ref.split('.')

    # Check if the base field exists in current model
    base_field = parts[0]
    if base_field not in model_fields:
        return False, f"Base field '{base_field}' not found"

    # For related fields, we assume they exist since we'd need to check
    # the comodel which requires more complex analysis
    return True, "Related field (assumed valid)"

def main():
    """Main validation function."""
    records_mgmt_path = "records_management/models"

    if not os.path.exists(records_mgmt_path):
        print(f"Error: {records_mgmt_path} not found")
        return 1

    all_models = {}
    issues = []

    print("=== @api.depends Validation ===\n")

    # First pass: collect all models and their fields
    for filename in os.listdir(records_mgmt_path):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(records_mgmt_path, filename)
            model_name, fields, inherited = extract_model_fields(file_path)
            if model_name:
                all_models[model_name] = {
                    'fields': fields,
                    'file': filename,
                    'inherited': inherited
                }

    print(f"Found {len(all_models)} models")

    # Second pass: validate @api.depends
    for filename in os.listdir(records_mgmt_path):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(records_mgmt_path, filename)

            # Get model info
            model_name, fields, inherited = extract_model_fields(file_path)
            if not model_name:
                continue

            # Get all @api.depends
            depends_list = extract_api_depends(file_path)

            if depends_list:
                print(f"\n📋 {model_name} ({filename}):")

                for dep in depends_list:
                    # Skip empty dependencies
                    if not dep.strip():
                        continue

                    # Validate the dependency
                    if '.' not in dep:
                        # Direct field
                        if dep not in fields:
                            issues.append({
                                'model': model_name,
                                'file': filename,
                                'dependency': dep,
                                'issue': f"Field '{dep}' not found in model '{model_name}'"
                            })
                            print(f"   ❌ {dep} - Field not found")
                        else:
                            print(f"   ✅ {dep}")
                    else:
                        # Related field - check base field exists
                        base_field = dep.split('.')[0]
                        if base_field not in fields:
                            issues.append({
                                'model': model_name,
                                'file': filename,
                                'dependency': dep,
                                'issue': f"Base field '{base_field}' not found in model '{model_name}'"
                            })
                            print(f"   ❌ {dep} - Base field '{base_field}' not found")
                        else:
                            print(f"   ✅ {dep}")

    # Report issues
    print(f"\n=== Summary ===")
    print(f"Models checked: {len(all_models)}")
    print(f"Issues found: {len(issues)}")

    if issues:
        print(f"\n🚨 CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  📁 {issue['file']} ({issue['model']})")
            print(f"     Dependency: '{issue['dependency']}'")
            print(f"     Issue: {issue['issue']}")
            print()
        return 1
    else:
        print("\n✅ All @api.depends validations passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
