#!/usr/bin/env python3
"""
Debug script to investigate specific @api.depends issues
"""

import os
import re
import sys

def extract_model_info(file_path):
    """Extract detailed model information"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract model name
        model_name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if not model_name_match:
            return None, {}, [], []

        model_name = model_name_match.group(1)

        # Extract field definitions
        fields = {}
        field_pattern = r"(\w+)\s*=\s*fields\.\w+"
        for match in re.finditer(field_pattern, content):
            field_name = match.group(1)
            fields[field_name] = True

        # Extract inheritance
        inherit_patterns = [
            r"_inherit\s*=\s*['\"]([^'\"]+)['\"]",
            r"_inherit\s*=\s*\[['\"]([^'\"]+)['\"]"
        ]
        inherited_models = []
        for pattern in inherit_patterns:
            for match in re.finditer(pattern, content):
                inherited_models.append(match.group(1))

        # Extract @api.depends
        depends_pattern = r"@api\.depends\(['\"]([^'\"]+)['\"](?:,\s*['\"]([^'\"]+)['\"])*\)"
        depends = []
        for match in re.finditer(depends_pattern, content):
            full_match = match.group(0)
            field_refs = re.findall(r"['\"]([^'\"]+)['\"]", full_match)
            depends.extend(field_refs)

        return model_name, fields, inherited_models, depends
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None, {}, [], []

def debug_container_retrieval_item():
    """Debug the specific container_retrieval_item issue"""

    print("=== Debugging container.retrieval.item ===\n")

    # Check the container retrieval item
    container_file = "records_management/models/container_retrieval_item.py"
    model_name, fields, inherited, depends = extract_model_info(container_file)

    print(f"Model: {model_name}")
    print(f"Defined fields: {list(fields.keys())}")
    print(f"Inherits from: {inherited}")
    print(f"@api.depends: {depends}")
    print()

    # Check the base class
    base_file = "records_management/models/retrieval_item_base.py"
    base_model, base_fields, base_inherited, base_depends = extract_model_info(base_file)

    print(f"Base Model: {base_model}")
    print(f"Base fields: {list(base_fields.keys())}")
    print(f"Base inherits from: {base_inherited}")
    print(f"Base @api.depends: {base_depends}")
    print()

    # Check if 'name' is in base fields
    if 'name' in base_fields:
        print("✅ 'name' field IS defined in the base class")
    else:
        print("❌ 'name' field is NOT defined in the base class")

    # Check dependencies that use 'name'
    name_deps = [dep for dep in depends if 'name' in dep.split('.')]
    if name_deps:
        print(f"\n📋 Dependencies referencing 'name': {name_deps}")
        for dep in name_deps:
            if dep == 'name':
                print(f"   - '{dep}': Direct reference to 'name' field")
            else:
                print(f"   - '{dep}': Related field reference")

    return 'name' in base_fields, depends

if __name__ == "__main__":
    os.chdir("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    debug_container_retrieval_item()
