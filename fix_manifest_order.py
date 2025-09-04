#!/usr/bin/env python3
"""
Script to analyze and fix Odoo manifest loading order for actions and menus.
Ensures all actions are defined before they're referenced by menus.
"""

import os
import re
from collections import defaultdict, deque

def find_action_definitions_and_references():
    """Find all action definitions and references in XML files."""
    action_definitions = {}  # action_id -> file_path
    action_references = defaultdict(list)  # action_id -> list of (file_path, line)

    # Walk through all XML files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Find action definitions
                    def_matches = re.findall(r'<record[^>]*id="([^"]*action[^"]*)"[^>]*model="ir\.actions\.', content)
                    for action_id in def_matches:
                        action_definitions[action_id] = file_path

                    # Find action references in menuitems
                    ref_matches = re.findall(r'<menuitem[^>]*action="([^"]*)"[^>]*>', content)
                    for action_id in ref_matches:
                        action_references[action_id].append((file_path, content.count(f'action="{action_id}"')))

                except Exception as e:
                    print(f"Error reading {file_path}: {e}")

    return action_definitions, action_references

def analyze_dependencies(action_definitions, action_references):
    """Analyze which files need to be loaded before others."""
    file_dependencies = defaultdict(list)  # file -> list of files it depends on

    for action_id, references in action_references.items():
        if action_id in action_definitions:
            def_file = action_definitions[action_id]
            for ref_file, _ in references:
                if ref_file != def_file:  # Don't add self-dependency
                    file_dependencies[ref_file].append(def_file)

    return file_dependencies

def topological_sort(files, dependencies):
    """Perform topological sort to determine loading order."""
    # Create graph
    graph = defaultdict(list)
    in_degree = {file: 0 for file in files}

    for file, deps in dependencies.items():
        for dep in deps:
            if dep in files:  # Only consider files in our manifest
                graph[dep].append(file)
                in_degree[file] += 1

    # Kahn's algorithm
    queue = deque([file for file in files if in_degree[file] == 0])
    result = []

    while queue:
        current = queue.popleft()
        result.append(current)

        for dependent in graph[current]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    # Check for cycles
    if len(result) != len(files):
        print("Warning: Circular dependencies detected!")
        # Add remaining files
        result.extend([f for f in files if f not in result])

    return result

def reorder_manifest():
    """Reorder the manifest based on action dependencies."""
    # Read current manifest
    with open('__manifest__.py', 'r') as f:
        content = f.read()

    # Extract data list
    data_match = re.search(r'"data":\s*\[(.*?)\]', content, re.DOTALL)
    if not data_match:
        print("Could not find data list in manifest")
        return

    data_content = data_match.group(1)

    # Extract individual file entries
    file_pattern = r'"([^"]*\.xml)"'
    files = re.findall(file_pattern, data_content)

    # Filter to only view files
    view_files = [f for f in files if f.startswith('views/')]

    print(f"Found {len(view_files)} view files to analyze")

    # Analyze dependencies
    action_defs, action_refs = find_action_definitions_and_references()
    dependencies = analyze_dependencies(action_defs, action_refs)

    print(f"Found {len(action_defs)} action definitions and {len(action_refs)} action references")

    # Perform topological sort
    try:
        sorted_files = topological_sort(view_files, dependencies)
        print("Successfully sorted files by dependencies")
    except Exception as e:
        print(f"Error during sorting: {e}")
        return

    # Reconstruct data list
    other_files = [f for f in files if not f.startswith('views/')]
    new_data_list = other_files + sorted_files

    # Create new data section
    new_data_content = ',\n        '.join(f'"{f}"' for f in new_data_list)

    # Replace in manifest
    new_content = content.replace(data_match.group(0), f'"data": [\n        {new_data_content}\n    ]')

    # Write back
    with open('__manifest__.py', 'w') as f:
        f.write(new_content)

    print("Manifest reordered successfully!")
    print("\nAction dependency analysis:")
    for action_id, refs in action_refs.items():
        if action_id in action_defs:
            def_file = os.path.basename(action_defs[action_id])
            print(f"✓ {action_id}: defined in {def_file}, referenced {len(refs)} times")

if __name__ == '__main__':
    os.chdir('records_management')
    reorder_manifest()
