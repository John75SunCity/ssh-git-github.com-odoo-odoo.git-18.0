#!/usr/bin/env python3
"""
Script to identify models that exist in the models directory but are not imported in __init__.py
"""

import os
import re
from pathlib import Path


def get_models_from_files(models_dir):
    """Get all model names from Python files in models directory"""
    models = []

    for file_path in Path(models_dir).glob("*.py"):
        if file_path.name == "__init__.py":
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for _name attribute
            import re

            name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
            if name_match:
                model_name = name_match.group(1)
                models.append((model_name, file_path.stem))

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return models


def get_imported_models(init_file):
    """Get all models imported in __init__.py"""
    imported_models = []

    with open(init_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the multi-line import block
    import_pattern = r"from \. import \(\s*([^)]+)\s*\)"
    match = re.search(import_pattern, content, re.DOTALL)

    if match:
        imports_block = match.group(1)
        # Split by comma and clean up
        import_lines = imports_block.split(",")
        for line in import_lines:
            # Remove comments and whitespace
            line = line.split("#")[0].strip()
            if line and not line.startswith("#"):
                imported_models.append(line)

    return imported_models


def main():
    models_dir = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models"
    init_file = "/Users/johncope/Documents/ssh-git-github.com-odoo-odoo.git-18.0/records_management/models/__init__.py"

    # Get all models from files
    file_models = get_models_from_files(models_dir)
    print(f"Found {len(file_models)} models in files")

    # Get imported models
    imported_models = get_imported_models(init_file)
    print(f"Found {len(imported_models)} imported models")

    # Find missing imports
    imported_set = set(imported_models)
    missing_models = []

    for model_name, file_name in file_models:
        if file_name not in imported_set:
            missing_models.append((model_name, file_name))

    print(f"\nFound {len(missing_models)} models not imported in __init__.py:")
    for model_name, file_name in sorted(missing_models):
        print(f"  {file_name} -> {model_name}")

    # Generate updated __init__.py content
    if missing_models:
        print("\nGenerating updated __init__.py content...")
        all_imports = sorted(imported_models + [file_name for _, file_name in missing_models])

        # Create the import block
        import_lines = []
        for i, imp in enumerate(all_imports):
            if i > 0 and i % 5 == 0:  # Add line break every 5 imports
                import_lines.append(f"    {imp},")
                import_lines.append("")
            else:
                import_lines.append(f"    {imp},")

        # Remove the last comma and add closing
        if import_lines and import_lines[-1].endswith(","):
            import_lines[-1] = import_lines[-1][:-1]

        import_block = "\n".join(import_lines)

        updated_content = f"""# -*- coding: utf-8 -*-
# Import addon models (sorted alphabetically by filename)
from . import (
{import_block}
)
"""

        print("\nUpdated __init__.py content generated.")
        print("You can copy this content to replace the current __init__.py file:")
        print("=" * 50)
        print(updated_content)
        print("=" * 50)


if __name__ == "__main__":
    main()
