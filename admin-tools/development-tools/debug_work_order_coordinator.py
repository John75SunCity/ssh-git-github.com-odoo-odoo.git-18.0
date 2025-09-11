#!/usr/bin/env python3
"""
Debug script to investigate work.order.coordinator @api.depends issues
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

        # Extract inheritance - using same logic as enhanced validation script
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

def debug_work_order_coordinator():
    """Debug the specific work.order.coordinator issue"""

    print("=== Debugging work.order.coordinator ===\n")

    # Check the work order coordinator
    coordinator_file = "records_management/models/work_order_coordinator.py"
    model_name, fields, inherited, depends = extract_model_info(coordinator_file)

    print(f"Model: {model_name}")
    print(f"Defined fields: {list(fields.keys())}")
    print(f"Inherits from: {inherited}")
    print(f"@api.depends: {depends}")
    print()

    # Check specific missing fields
    missing_fields = ['container_retrieval_ids', 'file_retrieval_ids', 'scan_retrieval_ids', 'destruction_ids']
    for field in missing_fields:
        if field in fields:
            print(f"✅ '{field}' field IS defined in the model")
        else:
            print(f"❌ '{field}' field is NOT defined in the model")

    # Check dependencies that use missing fields
    print(f"\n📋 All dependencies: {depends}")
    for dep in depends:
        base_field = dep.split('.')[0]
        if base_field in missing_fields:
            if base_field in fields:
                print(f"   ✅ '{dep}': Base field '{base_field}' found")
            else:
                print(f"   ❌ '{dep}': Base field '{base_field}' NOT found")

    return fields, depends

if __name__ == "__main__":
    os.chdir("/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0")
    debug_work_order_coordinator()
