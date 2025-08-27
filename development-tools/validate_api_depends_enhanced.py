#!/usr/bin/env python3
"""
Comprehensive validation script for @api.depends across all models.
Checks that all referenced fields in @api.depends actually exist.
Handles inheritance properly by resolving inherited fields.
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

        # Also check for inherited models - handle both single and multiple inheritance
        inherit_patterns = [
            r"_inherit\s*=\s*['\"]([^'\"]+)['\"]",  # Single inheritance
        ]
        inherited_models = []

        # Handle multiple inheritance in list format
        multi_inherit_match = re.search(r"_inherit\s*=\s*\[(.*?)\]", content, re.DOTALL)
        if multi_inherit_match:
            inherit_content = multi_inherit_match.group(1)
            inherit_items = re.findall(r"['\"]([^'\"]+)['\"]", inherit_content)
            inherited_models.extend(inherit_items)
        else:
            # Single inheritance
            for pattern in inherit_patterns:
                inherit_match = re.search(pattern, content)
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

        depends = []

        # Single line @api.depends
        depends_pattern = r"@api\.depends\(['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])*\)"
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

def resolve_inherited_fields(all_models):
    """Resolve inherited fields for all models"""
    def get_all_fields_recursive(model_name, visited=None):
        """Recursively get all fields including inherited ones"""
        if visited is None:
            visited = set()

        if model_name in visited or model_name not in all_models:
            return {}

        visited.add(model_name)
        model_info = all_models[model_name]
        all_fields = dict(model_info['fields'])

        # Add fields from inherited models
        for inherited_model in model_info['inherited']:
            inherited_fields = get_all_fields_recursive(inherited_model, visited)
            all_fields.update(inherited_fields)

        return all_fields

    for model_name, model_info in all_models.items():
        model_info['all_fields'] = get_all_fields_recursive(model_name)

    return all_models

def main():
    """Main validation function."""
    records_mgmt_path = "records_management/models"

    if not os.path.exists(records_mgmt_path):
        print(f"Error: {records_mgmt_path} not found")
        return 1

    all_models = {}
    issues = []

    print("=== @api.depends Validation (Enhanced with Inheritance) ===\n")

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

    # Resolve inherited fields
    all_models = resolve_inherited_fields(all_models)

    # Second pass: validate @api.depends
    for filename in os.listdir(records_mgmt_path):
        if filename.endswith('.py') and filename != '__init__.py':
            file_path = os.path.join(records_mgmt_path, filename)

            # Get model info
            model_name, fields, inherited = extract_model_fields(file_path)
            if not model_name:
                continue

            # Get resolved fields (including inherited)
            all_fields = all_models.get(model_name, {}).get('all_fields', fields)

            # Get all @api.depends
            depends_list = extract_api_depends(file_path)

            if depends_list:
                print(f"\n📋 {model_name} ({filename}):")
                if inherited:
                    print(f"   Inherits from: {inherited}")

                for dep in depends_list:
                    # Skip empty dependencies
                    if not dep.strip():
                        continue

                    # Validate the dependency
                    if '.' not in dep:
                        # Direct field
                        if dep not in all_fields:
                            issues.append({
                                'model': model_name,
                                'file': filename,
                                'dependency': dep,
                                'issue': f"Field '{dep}' not found in model '{model_name}' (including inherited fields)"
                            })
                            print(f"   ❌ {dep} - Field not found")
                        else:
                            # Check if it's inherited
                            source = "direct" if dep in fields else "inherited"
                            print(f"   ✅ {dep} ({source})")
                    else:
                        # Related field - check base field exists
                        base_field = dep.split('.')[0]
                        if base_field not in all_fields:
                            issues.append({
                                'model': model_name,
                                'file': filename,
                                'dependency': dep,
                                'issue': f"Base field '{base_field}' not found in model '{model_name}' (including inherited fields)"
                            })
                            print(f"   ❌ {dep} - Base field '{base_field}' not found")
                        else:
                            # Check if base field is inherited
                            source = "direct" if base_field in fields else "inherited"
                            print(f"   ✅ {dep} (base field {source})")

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
